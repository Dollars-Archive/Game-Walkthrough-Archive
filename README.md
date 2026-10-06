# Dollars Archive 공략집

Dollars Archive가 직접 작성한 게임 공략만 모읍니다.

[공략집 모음](https://dollars-archive.github.io/Game-Walkthrough-Archive/) · [한글패치 모음](https://dollars-archive.github.io/Dollars-Archive/)

## 공략 등록

지침 파일을 따로 첨부할 필요 없이, GitHub에 연결된 GPT·Codex에 공략 파일만 첨부하고 게임 이름과 함께 요청하세요.

> @GitHub 지금 첨부한 공략집 티어즈 투 티아라 2에 등록해줘.

게임명과 기종이 파일에 없으면 함께 적어주세요. GPT는 이 저장소와 각 한패 저장소에 연결된 [등록 지침](REGISTER-GUIDE.md)을 읽고 등록·업데이트·배포 확인을 진행합니다. 실제로 다른 GPT가 어떤 파일부터 읽는지까지 GitHub 문서로 강제할 수는 없습니다.

### 직접 등록하는 경우

1. 직접 만든 Markdown 또는 PDF 파일을 `guides/` 아래에 업로드합니다.
2. `guides.yml`의 `guides` 목록에 아래처럼 등록합니다. 처음에는 `guides: []`를 `guides:`로 바꿉니다.

```yaml
guides:
  - id: eve-zero-story
    patch_repo: eve-zero-kr-patch
    title: EVE ZERO 스토리·분기 공략
    category: 스토리·분기
    file: guides/eve-zero/story.md
    original: true
```

`original: true`는 직접 작성한 공략이라는 확인입니다. 등록된 파일이 없거나 확인값이 없으면 게시하지 않습니다. 파일 이름은 영문과 하이픈을 권장합니다.

한글패치 저장소와 연결하면 게임명·기종·표지를 자동으로 가져옵니다. 패치가 없는 게임은 `patch_repo: ""`와 함께 `game`, `platforms`를 입력하면 됩니다.

```yaml
  - id: my-game-guide
    patch_repo: ""
    game: 게임 이름
    platforms: [PC]
    title: 직접 만든 공략
    category: 전체 공략
    file: guides/my-game/guide.pdf
    original: true
```

등록하거나 공략 파일을 수정하면 Actions가 대문과 읽기 페이지를 생성합니다. Markdown은 웹에서 읽는 페이지로 만들고 PDF는 바로 열립니다. 같은 게임 공략이 여러 개면 한패 카드에서 해당 게임의 공략 목록을 엽니다.

공략을 등록·수정하면 다운로드용 ZIP도 자동으로 만들어 공략별 GitHub 릴리즈에 첨부합니다. 대문의 다운로드 버튼은 현재 공략의 ZIP으로 연결하며, 오른쪽 숫자는 해당 공략의 모든 수정본 파일을 합친 누적 다운로드 수입니다. 같은 파일은 다시 업로드하지 않고 이전 파일은 집계 보존을 위해 유지합니다. 공략 읽기 횟수와 집계 시작 전의 다운로드는 포함하지 않습니다.

숫자는 대문을 열거나 새로고침할 때 GitHub에서 갱신합니다. API 연결이 안 되면 매시 23분 자동화가 수집한 마지막 값을 표시합니다. 수정본 등록은 기존 id를 유지해야 누적 집계도 이어집니다.

한패 허브를 새로고침하면 최신 공략 목록을 읽어 `공략집 ✓`와 링크를 갱신합니다. 프로필과 저장 데이터는 매시 23분 수집 때 반영되며 GitHub 예약 실행은 지연될 수 있습니다. 자동화를 위한 별도 개인 토큰은 사용하지 않습니다.

## 등록된 공략

<!-- WALKTHROUGHS:START -->
- [라디아타 스토리즈 — 라디아타 스토리즈 · 동료 177명 완전 영입 체크리스트](https://dollars-archive.github.io/Game-Walkthrough-Archive/guides/radiata-stories-177-guide/radiata-stories-177-guide.html)
- [비너스 앤 브레이브스 — 비너스 앤 브레이브스 · 100년의 여정 플로우 가이드](https://dollars-archive.github.io/Game-Walkthrough-Archive/guides/venus-and-braves-guide/venus-and-braves-guide.html)
- [티어즈 투 티아라 2 — 티어즈 투 티아라 2 한국어 완전 공략집](https://dollars-archive.github.io/Game-Walkthrough-Archive/guides/tears-to-tiara-2-kr-patch/tears-to-tiara-2-complete.html)
<!-- WALKTHROUGHS:END -->
