#!/usr/bin/env python
"""
"크랭크 오토" wake word 모델 학습 및 ONNX 내보내기.

사전 준비:
  uv run tools/record_samples.py --type positive  (최소 15개)
  uv run tools/record_samples.py --type negative  (최소 15개)

사용법:
  uv run tools/train_wake_word.py

출력:
  wake_word/crank_otto.onnx  —  openwakeword Model 클래스와 호환되는 ONNX 모델
"""

import audioop
import wave
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.utils import resample

from openwakeword.utils import AudioFeatures

SR = 16000
CHUNK = 1280           # 80ms at 16kHz — openwakeword 스트리밍 청크 크기
WINDOW_SIZE = 32       # openwakeword 모델 입력 크기 (32 frames × 96 dims, ~2.56초 context)
FEAT_DIM = 96
# 충분한 새 프레임을 얻기 위해 최소 50청크 분량의 오디오 필요 (mel 워밍업 ~10청크 + 32프레임)
MIN_SAMPLES = 50 * CHUNK  # ~4초
OUTPUT_PATH = Path("wake_word/crank_otto.onnx")
POS_DIR = Path("wake_word/training_data/positive")
NEG_DIR = Path("wake_word/training_data/negative")


# ── 오디오 로딩 ──────────────────────────────────────────────────────────────

def load_wav(path: Path) -> np.ndarray:
    """WAV 파일을 16kHz mono int16로 로드. 필요 시 자동 변환."""
    with wave.open(str(path), 'rb') as wf:
        n_ch = wf.getnchannels()
        src_sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16)
    if n_ch == 2:
        audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
    if src_sr != SR:
        resampled, _ = audioop.ratecv(audio.tobytes(), 2, 1, src_sr, SR, None)
        audio = np.frombuffer(resampled, dtype=np.int16)

    # 최소 길이 보장: 타일 반복 패딩
    if len(audio) < MIN_SAMPLES:
        repeats = MIN_SAMPLES // len(audio) + 1
        audio = np.tile(audio, repeats)[:MIN_SAMPLES]

    return audio


# ── 임베딩 추출 (추론 파이프라인과 동일한 스트리밍 방식) ──────────────────────

def extract_windows(audio_i16: np.ndarray) -> np.ndarray:
    """
    오디오 → training windows. shape: (N_windows, WINDOW_SIZE, FEAT_DIM)

    AudioFeatures.__call__()은 int16 PCM을 요구한다.
    float32로 피드하면 mel spectrogram 모델이 무음으로 해석해 임베딩이 항상 동일해진다.
    """
    af = AudioFeatures(inference_framework='onnx')
    initial_len = len(af.feature_buffer)

    windows = []
    for i in range(0, len(audio_i16) - CHUNK + 1, CHUNK):
        af(audio_i16[i:i+CHUNK])
        new_count = len(af.feature_buffer) - initial_len
        if new_count >= WINDOW_SIZE:
            feat = af.feature_buffer[-WINDOW_SIZE:].copy().astype(np.float32)
            windows.append(feat)

    return np.array(windows, dtype=np.float32) if windows else np.empty((0, WINDOW_SIZE, FEAT_DIM), dtype=np.float32)


# ── ONNX 내보내기 ─────────────────────────────────────────────────────────────

def build_onnx(clf: MLPClassifier) -> onnx.ModelProto:
    """
    sklearn MLPClassifier (hidden_layer_sizes=(128,)) →
    ONNX 모델 (input: (1,WINDOW_SIZE,FEAT_DIM), output: (1,1))

    openwakeword Model 클래스는 get_inputs()[0].name을 동적으로 읽으므로
    입력/출력 이름은 자유롭게 지정해도 됩니다.
    """
    assert len(clf.coefs_) == 2, "hidden_layer_sizes=(128,) 단일 은닉층만 지원합니다"

    W1 = clf.coefs_[0].astype(np.float32)
    b1 = clf.intercepts_[0].astype(np.float32)
    W2 = clf.coefs_[1].astype(np.float32)
    b2 = clf.intercepts_[1].astype(np.float32)

    def init(name, arr):
        return numpy_helper.from_array(arr, name=name)

    nodes = [
        helper.make_node('Reshape', ['x', 'flat_shape'], ['flat']),
        helper.make_node('MatMul',  ['flat', 'W1'], ['mm1']),
        helper.make_node('Add',     ['mm1', 'b1'], ['a1']),
        helper.make_node('Relu',    ['a1'], ['r1']),
        helper.make_node('MatMul',  ['r1', 'W2'], ['mm2']),
        helper.make_node('Add',     ['mm2', 'b2'], ['a2']),
        helper.make_node('Sigmoid', ['a2'], ['output']),
    ]

    graph = helper.make_graph(
        nodes,
        'crank_otto',
        inputs=[helper.make_tensor_value_info('x', TensorProto.FLOAT, [1, WINDOW_SIZE, FEAT_DIM])],
        outputs=[helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 1])],
        initializer=[
            numpy_helper.from_array(np.array([1, WINDOW_SIZE * FEAT_DIM], dtype=np.int64), 'flat_shape'),
            init('W1', W1),
            init('b1', b1),
            init('W2', W2),
            init('b2', b2),
        ],
    )

    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 13)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    return model


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    pos_files = sorted(POS_DIR.glob('*.wav')) if POS_DIR.exists() else []
    neg_files = sorted(NEG_DIR.glob('*.wav')) if NEG_DIR.exists() else []

    if len(pos_files) < 5:
        print(f"오류: positive 샘플이 {len(pos_files)}개입니다 (최소 5개 필요)")
        print("  uv run tools/record_samples.py --type positive")
        return
    if len(neg_files) < 5:
        print(f"오류: negative 샘플이 {len(neg_files)}개입니다 (최소 5개 필요)")
        print("  uv run tools/record_samples.py --type negative")
        return

    print(f"positive 파일: {len(pos_files)}개")
    print(f"negative 파일: {len(neg_files)}개")

    print("\n임베딩 추출 중 (스트리밍 방식)...")
    X_pos, X_neg = [], []

    for f in pos_files:
        wins = extract_windows(load_wav(f))
        if len(wins) == 0:
            print(f"  [SKIP] {f.name}: windows 없음")
            continue
        X_pos.extend(wins)

    for f in neg_files:
        wins = extract_windows(load_wav(f))
        if len(wins) == 0:
            continue
        X_neg.extend(wins)

    if len(X_pos) == 0:
        print("오류: positive window가 하나도 없습니다. 샘플을 다시 녹음하세요.")
        return

    X_pos = np.array(X_pos, dtype=np.float32)
    X_neg = np.array(X_neg, dtype=np.float32)

    print(f"positive windows: {len(X_pos)}")
    print(f"negative windows: {len(X_neg)}")

    # 클래스 불균형 보정
    if len(X_pos) < len(X_neg):
        X_pos = resample(X_pos, n_samples=len(X_neg), replace=True, random_state=42)
        print(f"positive 오버샘플링 → {len(X_pos)}개")
    elif len(X_neg) < len(X_pos):
        X_neg = resample(X_neg, n_samples=len(X_pos), replace=True, random_state=42)
        print(f"negative 오버샘플링 → {len(X_neg)}개")

    X = np.vstack([
        X_pos.reshape(len(X_pos), -1),
        X_neg.reshape(len(X_neg), -1),
    ])
    y = np.array([1] * len(X_pos) + [0] * len(X_neg))

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"\n학습 데이터: {len(X_train)}개 | 검증 데이터: {len(X_val)}개")

    print("\nMLP 학습 중...")
    clf = MLPClassifier(
        hidden_layer_sizes=(128,),
        activation='relu',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        verbose=True,
    )
    clf.fit(X_train, y_train)

    val_proba = clf.predict_proba(X_val)[:, 1]
    recall      = (val_proba[y_val == 1] >= 0.5).mean()
    specificity = (val_proba[y_val == 0] < 0.5).mean()
    print(f"\n검증 recall    (positive 감지율): {recall:.1%}")
    print(f"검증 specificity (오탐 억제율): {specificity:.1%}")

    if recall < 0.6:
        print("[WARNING] recall이 낮습니다. positive 샘플을 더 녹음하거나 threshold를 낮추세요.")
    if specificity < 0.9:
        print("[WARNING] 오탐이 많을 수 있습니다. negative 샘플을 더 다양하게 녹음하세요.")

    print("\nONNX 내보내기...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    model = build_onnx(clf)
    onnx.save(model, str(OUTPUT_PATH))
    print(f"저장됨: {OUTPUT_PATH}")

    import onnxruntime as ort
    sess = ort.InferenceSession(str(OUTPUT_PATH))
    dummy = np.random.randn(1, WINDOW_SIZE, FEAT_DIM).astype(np.float32)
    out = sess.run(None, {sess.get_inputs()[0].name: dummy})
    print(f"추론 확인: output shape={out[0].shape}  샘플 score={out[0][0, 0]:.4f}")
    print("\n완료! 봇을 실행하면 crank_otto.onnx 모델이 자동으로 로드됩니다.")


if __name__ == '__main__':
    main()
