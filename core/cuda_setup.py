"""Windows에서 faster-whisper(CTranslate2)가 CUDA DLL을 찾도록 경로를 등록한다.

CTranslate2 4.x는 cublas64_12.dll / cudnn64_9.dll / cudart64_12.dll 등을
런타임에 LoadLibrary로 로드한다. Windows에는 이 DLL이 시스템 PATH에 없으므로
nvidia-cublas-cu12 / nvidia-cudnn-cu12 / nvidia-cuda-runtime-cu12 pip 패키지가
설치한 bin 디렉토리를 PATH와 DLL 검색 경로에 추가해야 한다.

stt.py가 faster_whisper를 import하기 *전에* setup()을 호출할 것.
Windows가 아니거나 nvidia 패키지가 없으면(예: Linux GPU, CPU 환경) 조용히 no-op.
"""
import os
import sys
import logging

log = logging.getLogger(__name__)

_done = False


def setup() -> None:
    global _done
    if _done or sys.platform != "win32":
        return
    _done = True

    try:
        import nvidia  # nvidia-*-cu12 패키지가 만드는 네임스페이스 패키지
    except ImportError:
        log.debug("nvidia CUDA pip packages not installed — skip DLL setup")
        return

    # nvidia는 네임스페이스 패키지(PEP 420) → __file__은 None, __path__를 사용
    bins = []
    for base in list(nvidia.__path__):
        for sub in ("cuda_runtime", "cublas", "cudnn", "cuda_nvrtc"):
            d = os.path.join(base, sub, "bin")
            if os.path.isdir(d):
                bins.append(d)

    if not bins:
        log.debug("no nvidia bin dirs found under %s", base)
        return

    os.environ["PATH"] = os.pathsep.join(bins) + os.pathsep + os.environ.get("PATH", "")
    for d in bins:
        os.add_dll_directory(d)
    log.info("CUDA DLL path registered (%d dirs)", len(bins))
