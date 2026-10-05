# Dollars Archive 공략집

Dollars Archive가 직접 작성한 게임 공략만 모읍니다.

[공략집 모음](https://dollars-archive.github.io/Game-Walkthrough-Archive/) · [한글패치 모음](https://dollars-archive.github.io/Dollars-Archive/)

## 공략 등록

파일을 GPT·Codex에 첨부하고 아래 요청문을 보내면 됩니다. GitHub 쓰기 권한이 있는 환경에서 실행하세요.

> 내가 직접 만든 공략집이야. [등록 지침](https://github.com/Dollars-Archive/Game-Walkthrough-Archive/blob/main/REGISTER-GUIDE.md)을 읽고 이 파일을 등록해줘. 기존 공략의 수정본이면 업데이트하고, 공략 대문과 한패 대문 연결·배포까지 확인해줘.

게임명과 기종이 파일에 없으면 함께 적어주세요. [GPT용 전체 지침과 등록 도구 사용법](REGISTER-GUIDE.md)을 준비해 두었습니다.

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

한패 허브를 새로고침하면 최신 공략 목록을 읽어 `공략집 ✓`와 링크를 갱신합니다. 프로필과 저장 데이터는 매시 23분 수집 때 반영되며 GitHub 예약 실행은 지연될 수 있습니다. 자동화를 위한 별도 개인 토큰은 사용하지 않습니다.

## 등록된 공략

<!-- WALKTHROUGHS:START -->
아직 등록된 공략이 없습니다.
<!-- WALKTHROUGHS:END -->
