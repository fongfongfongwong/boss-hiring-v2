"""Prompt templates for resume analysis."""

EXTRACT_SYSTEM = """\
你是一位专业的简历解析专家。请从以下简历文本中提取结构化信息。

以 JSON 格式回复：
{
  "name": "姓名",
  "phone": "手机号",
  "email": "邮箱",
  "education": [
    {"school": "学校", "degree": "学位", "major": "专业", "start_year": "开始年", "end_year": "结束年"}
  ],
  "work_experience": [
    {"company": "公司", "title": "职位", "start_date": "开始日期", "end_date": "结束日期", "description": "工作描述"}
  ],
  "projects": [
    {"name": "项目名", "role": "角色", "description": "描述", "tech_stack": ["技术1"]}
  ],
  "skills": ["技能1", "技能2"],
  "certifications": ["证书1"],
  "languages": ["语言能力1"],
  "summary": "一句话概括候选人的核心竞争力"
}

注意：
1. 尽可能完整提取所有信息
2. 如果某个字段信息缺失，留空字符串或空列表
3. 只返回 JSON
"""

EXTRACT_USER = """\
请解析以下简历文本：

{resume_text}
"""

SCORE_SYSTEM = """\
你是一位资深的技术招聘评估专家。请根据岗位要求和评分标准，对候选人的简历进行
多维度评分。

以 JSON 格式回复：
{
  "skill_match": 0-100,
  "experience_relevance": 0-100,
  "education_fit": 0-100,
  "project_quality": 0-100,
  "overall_recommendation": 0-100,
  "strengths": ["亮点1", "亮点2", "亮点3"],
  "weaknesses": ["不足1", "不足2"],
  "reasoning": "详细的评分理由（200字以内）"
}

评分标准：
- skill_match (技能匹配): 候选人技能与岗位要求技能的覆盖率和深度
- experience_relevance (经验相关): 过往工作和项目与目标岗位的相关程度
- education_fit (学历契合): 学历层次 + 专业方向与岗位要求的匹配度
- project_quality (项目质量): 项目的复杂度、影响力、技术深度
- overall_recommendation (综合推荐): 综合考虑所有因素后的整体推荐度

只返回 JSON。
"""

SCORE_USER = """\
目标岗位：
{jd_summary}

岗位评分标准：
{scorecard}

候选人结构化简历信息：
{extracted_resume}

请进行多维度评分。
"""
