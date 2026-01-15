import os

from docx import Document


class RequirementDocumentParser:
    """需求文档解析器"""

    def __init__(self, file_path):
        self.file_path = file_path
        # 文件后缀
        self.file_extension = os.path.splitext(self.file_path)[1].lower()

    def get_document_content(self):
        """
        获取需求文档内容
        支持 docx 和 md 格式
        """

        if self.file_extension == ".docx":
            document = Document(self.file_path)

            content = []

            for para in document.paragraphs:
                text = para.text.strip()
                if text:
                    content.append(text)

            return "\n".join(content)

        elif self.file_extension == ".md":
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            raise ValueError(f"不支持的文件格式: {self.file_extension}")


    def handle_picture(self):
        """处理需求文档的图片"""
        pass
