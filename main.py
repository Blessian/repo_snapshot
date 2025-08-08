# -*- coding: utf-8 -*-
"""
프로젝트 문서 자동 생성 스크립트 (v4)

기능:
- 커맨드 라인 인자(argument)로 대상 프로젝트의 루트 디렉토리 경로를 받습니다.
- 'config.json' 설정 파일을 읽어 제외할 디렉토리/파일 및 스타일을 적용합니다.
- Pygments를 사용하여 소스 코드를 문법에 맞게 하이라이팅합니다.
- 문서 상단에 클릭 가능한 목차(Table of Contents)를 추가합니다.
- 최종 결과를 WeasyPrint를 사용하여 하나의 PDF 파일로 만듭니다.

수정사항 (v4):
- PDF 출력 스타일(CSS)을 개선하여 가독성을 높였습니다.
- 기본 폰트 크기를 줄이고, 긴 코드 라인이 페이지를 벗어나지 않도록 자동 줄바꿈 처리를 강화했습니다.

사용법:
1. 'config.json'과 'requirements.txt' 파일이 있는지 확인합니다.
2. 터미널에서 'pip install -r requirements.txt'를 실행하여 라이브러리를 설치합니다.
3. 'python main.py [프로젝트 경로]' 형식으로 실행합니다.
4. 스크립트가 실행된 위치에 'config.json'에 정의된 이름으로 PDF 파일이 생성됩니다.
"""

# --- 종속성 임포트 ---
# 내장 모듈
import argparse
import json
from pathlib import Path

# 라이브러리 모듈
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from weasyprint import HTML, CSS

# --- 설정 로드 ---
try:
    # 설정 파일을 열고 내용을 로드합니다.
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("오류: 'config.json' 파일을 찾을 수 없습니다. 스크립트를 종료합니다.")
    exit()
except json.JSONDecodeError:
    print("오류: 'config.json' 파일의 형식이 올바르지 않습니다. 스크립트를 종료합니다.")
    exit()

# 설정 값들을 변수로 할당합니다.
OUTPUT_PDF_NAME = config.get("output_pdf_name", "project_documentation.pdf")
PYGMENTS_STYLE = config.get("pygments_style", "default")
EXCLUDE_DIRS = set(config.get("exclude_dirs", []))
EXCLUDE_FILES = set(config.get("exclude_files", []))


def is_excluded(path: Path, root_path: Path) -> bool:
    """
    주어진 경로가 제외 목록에 포함되는지 확인합니다.
    경로는 root_path에 대한 상대 경로를 기준으로 검사합니다.
    """
    if path.name in EXCLUDE_FILES:
        return True
    try:
        relative_parts = path.relative_to(root_path).parts
        return any(part in EXCLUDE_DIRS for part in relative_parts)
    except ValueError:
        return True


def is_binary(path: Path) -> bool:
    """
    파일이 텍스트 파일이 아닌 바이너리 파일인지 간단하게 확인합니다.
    'utf-8'로 디코딩을 시도하여 실패하면 바이너리 파일로 간주합니다.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(1024)
        return False
    except UnicodeDecodeError:
        print(f"알림: 바이너리 파일로 추정되어 건너뜁니다 - {path}")
        return True
    except Exception as e:
        print(f"파일 읽기 오류 '{path}': {e}")
        return True


def main():
    """메인 실행 함수"""
    # 1. 커맨드 라인 인자 파서 설정 및 파싱
    parser = argparse.ArgumentParser(
        description="프로젝트 디렉토리의 파일들을 스캔하여 하나의 PDF 문서로 변환합니다."
    )
    parser.add_argument(
        "project_path",
        type=str,
        help="문서화할 프로젝트의 루트 디렉토리 경로"
    )
    args = parser.parse_args()
    project_path = Path(args.project_path)

    # 2. 경로 유효성 검사
    if not project_path.is_dir():
        print(f"오류: '{args.project_path}'는 유효한 디렉토리가 아닙니다. 스크립트를 종료합니다.")
        return

    print(f"'{project_path.resolve()}' 디렉토리에 대한 문서 생성을 시작합니다...")

    # 3. 모든 파일 탐색 및 필터링
    all_files = [p for p in project_path.rglob("*") if p.is_file()]
    target_files = [
        p for p in all_files if not is_excluded(p, project_path) and not is_binary(p)
    ]
    print(f"총 {len(target_files)}개의 파일을 처리합니다.")

    # 4. HTML 콘텐츠 및 목차 생성
    html_parts = []
    toc_items = []
    formatter = HtmlFormatter(
        style=PYGMENTS_STYLE, full=True, cssclass="highlight", linenos="inline"
    )

    for i, file_path in enumerate(target_files):
        relative_path = file_path.relative_to(project_path)
        relative_path_str = relative_path.as_posix()
        anchor = f"file-{i}"
        toc_items.append((relative_path_str, anchor))

        try:
            content = file_path.read_text(encoding="utf-8")
            try:
                lexer = get_lexer_for_filename(file_path.name, stripall=True)
            except Exception:
                lexer = TextLexer()

            highlighted_code = highlight(content, lexer, formatter)

            file_html = f"""
            <div id="{anchor}" class="file-container">
                <h2><b>{relative_path_str}</b></h2>
                {highlighted_code}
            </div>
            """
            html_parts.append(file_html)

        except Exception as e:
            print(f"'{file_path}' 처리 중 오류 발생: {e}")

    # 5. 목차(TOC) HTML 생성
    toc_html_list = [
        f'<li><a href="#{anchor}">{path_str}</a></li>'
        for path_str, anchor in toc_items
    ]
    toc_html = f"""
    <div class="toc">
        <h1>{project_path.name} - 프로젝트 문서</h1>
        <h2>목차 (Table of Contents)</h2>
        <ul>
            {''.join(toc_html_list)}
        </ul>
    </div>
    """

    # 6. 전체 HTML 문서 조합 (스타일 개선)
    final_css = f"""
    {formatter.get_style_defs()}
    /* --- 기본 및 타이포그래피 설정 --- */
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        font-size: 9pt; /* 기본 폰트 크기를 줄여 더 많은 내용을 담도록 조정 */
        line-height: 1.4;
    }}
    h1, h2 {{
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        font-weight: 600;
    }}
    h1 {{ font-size: 18pt; }}
    h2 {{ font-size: 14pt; }}

    /* --- 목차(TOC) 스타일 --- */
    .toc {{
        border-bottom: 2px solid #ccc;
        padding-bottom: 20px;
        margin-bottom: 20px;
        page-break-after: always; /* 목차 다음에 항상 페이지를 넘김 */
    }}
    .toc ul {{ list-style-type: none; padding-left: 0; }}
    .toc a {{ text-decoration: none; color: #007bff; }}
    .toc a:hover {{ text-decoration: underline; }}

    /* --- 파일 컨테이너 스타일 --- */
    .file-container {{ page-break-before: auto; }}

    /* --- 코드 하이라이팅 블록 스타일 (가독성 개선의 핵심) --- */
    .highlight pre {{
        white-space: pre-wrap !important;  /* 자동 줄바꿈을 허용하여 내용이 페이지를 벗어나지 않도록 함 */
        word-wrap: break-word;         /* 긴 단어나 URL을 강제로 줄바꿈 처리 */
        font-size: 8.5pt;              /* 코드 폰트 크기를 본문보다 약간 작게 설정 */
    }}
    .highlight table {{
        width: 100% !important;
        border-collapse: collapse;
        table-layout: fixed; /* 테이블 레이아웃을 고정하여 너비 문제 방지 */
    }}
    .highlight .linenos {{
        color: #999;
        padding-right: 10px;
        user-select: none; /* 줄 번호는 선택되지 않도록 처리 */
        width: 35px; /* 줄 번호 컬럼의 너비를 고정 */
        text-align: right;
    }}
    .highlight .code {{
        width: calc(100% - 40px); /* 코드 컬럼이 남은 공간을 모두 사용하도록 계산 */
    }}
    """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Project Documentation: {project_path.name}</title>
        <style>{final_css}</style>
    </head>
    <body>
        {toc_html}
        {''.join(html_parts)}
    </body>
    </html>
    """

    # 7. PDF로 변환
    output_file = Path(OUTPUT_PDF_NAME)
    print(f"'{output_file.name}' 파일로 저장 중입니다...")
    try:
        HTML(string=full_html, base_url=str(project_path)).write_pdf(
            output_file, stylesheets=[CSS(string="@page { size: A4; margin: 1.8cm; }")]
        )
        print(f"PDF 생성이 완료되었습니다! -> {output_file.resolve()}")
    except Exception as e:
        print(f"PDF 생성 중 심각한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
