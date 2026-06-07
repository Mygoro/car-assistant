"""전시용 memory 생성: memory.md에서 [개인전용] 줄을 제거해 memory_exhibition.md를 만든다.

전시 전날 1회 실행:
    uv run tools/strip_personal.py
그 뒤 config.yaml의 memory_mode를 exhibition으로 변경.
"""
from pathlib import Path

src = Path("core/memory.md")
dst = Path("core/memory_exhibition.md")

lines = src.read_text(encoding="utf-8").splitlines()

# [개인전용] 줄 제거
filtered = [l for l in lines if "[개인전용]" not in l]

# 섹션 헤더(## ...) 다음에 바로 다른 헤더나 EOF가 오는 빈 섹션 제거
result = []
i = 0
while i < len(filtered):
    line = filtered[i]
    if line.startswith("## "):
        # 헤더 다음 비어있지 않은 줄이 있는지 확인 (빈 줄 건너뜀)
        j = i + 1
        while j < len(filtered) and filtered[j].strip() == "":
            j += 1
        if j >= len(filtered) or filtered[j].startswith("#"):
            i = j  # 빈 섹션 건너뜀
            continue
    result.append(line)
    i += 1

# 연속 빈 줄 정리
out = []
prev_blank = False
for line in result:
    is_blank = line.strip() == ""
    if is_blank and prev_blank:
        continue
    out.append(line)
    prev_blank = is_blank

dst.write_text("\n".join(out), encoding="utf-8")
removed = len(lines) - len(out)
print(f"생성 완료: {dst} ({len(out)}줄, 원본 {len(lines)}줄에서 {removed}줄 제거)")
