"""测试 AI 标题识别完整流程（通过 API）。"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 测试文档路径（无标题样式）
TEST_DOCX_PATH = "/tmp/test_no_heading.docx"

def upload_document(username: str = "admin", password: str = "admin123456"):
    """上传测试文档并获取 doc_id。"""
    # 1. 登录获取 token
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password}
    )
    if login_resp.status_code != 200:
        print(f"登录失败：{login_resp.text}")
        return None

    token = login_resp.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 上传文档
    with open(TEST_DOCX_PATH, "rb") as f:
        upload_resp = requests.post(
            f"{BASE_URL}/api/documents/upload",
            headers=headers,
            files={"file": ("test_no_heading.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

    if upload_resp.status_code != 200:
        print(f"上传失败：{upload_resp.text}")
        return None

    doc_id = upload_resp.json()["data"]["id"]
    print(f"文档上传成功，doc_id: {doc_id}")
    return doc_id, token

def extract_structure(doc_id: str, token: str):
    """测试提取结构 API。"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== 调用 extract-structure API ===")
    resp = requests.post(
        f"{BASE_URL}/api/ai/extract-structure",
        headers=headers,
        json={"doc_id": doc_id}
    )

    print(f"响应状态码：{resp.status_code}")

    if resp.status_code != 200:
        print(f"响应内容：{resp.text}")
        return None

    result = resp.json()
    print(f"\n提取结果:")

    if result.get("status") == "ai_failed":
        print(f"AI 处理失败：{result.get('message')}")
        return None

    structure = result.get("structure", {})
    print(f"文档标题：{structure.get('title')}")

    sections = structure.get("sections", [])
    heading_count = sum(1 for s in sections if s.get("paragraph_type") == "heading")
    print(f"总 sections 数：{len(sections)}")
    print(f"识别的标题数：{heading_count}")

    # 显示识别出的标题
    print("\n识别的标题:")
    for i, sec in enumerate(sections):
        if sec.get("paragraph_type") == "heading":
            level = sec.get("level", "?")
            text = sec.get("text", "")[:50]
            print(f"  [{i}] H{level}: {text}")

    # 显示前几个 sections 的详细信息
    print("\n前 5 个 sections 详情:")
    for i, sec in enumerate(sections[:5]):
        ptype = sec.get("paragraph_type")
        text = sec.get("text", "")[:30]
        level = sec.get("level", 0)
        print(f"  [{i}] type={ptype}, level={level}, text={text}")

    return result

if __name__ == "__main__":
    print("=== AI 标题识别 API 测试 ===\n")

    # 上传文档
    result = upload_document()
    if not result:
        print("测试失败：无法上传文档")
        exit(1)

    doc_id, token = result

    # 提取结构
    extract_structure(doc_id, token)

    print("\n=== 测试完成 ===")
