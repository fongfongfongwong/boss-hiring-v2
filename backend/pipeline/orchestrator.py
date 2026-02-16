"""Pipeline Orchestrator – connects all 5 modules into a single automated flow.

Flow: Position Analysis → RPA Browser → Search & Greet → Resume Analysis → Contact Follow-up
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Coroutine

from sqlalchemy.orm import Session

from analyzer.position_analyzer import analyze_position
from communicator.chat_manager import analyze_reply, generate_followup
from communicator.contact_followup import generate_contact_request, process_contact_reply
from communicator.greeter import generate_greeting
from communicator.matcher import pre_match_candidate
from communicator.resume_collector import collect_resume
from database.db import SessionLocal
from database.models import (
    Candidate,
    ChatMessage,
    ContactInfo,
    Position,
    RecruitTask,
    Resume,
)
from pipeline.events import *
from pipeline.events import PipelineEvent
from pipeline.task_manager import TaskControl
from resume_analysis.extractor import extract_resume_info
from resume_analysis.parser import parse_resume
from resume_analysis.scorer import generate_report, score_resume
from resume_analysis.storage import save_resume_to_db
from rpa.anti_detect import apply_stealth
from rpa.browser_engine import BrowserEngine
from rpa.human_simulator import random_delay
from rpa.page_actions import (
    click_candidate_card,
    get_candidate_cards,
    get_candidate_profile,
    navigate_to_chat,
    navigate_to_search,
    scroll_to_load_more,
    search_candidates,
    send_chat_message,
    send_greeting,
)
from utils.config import get_config, get_qualified_threshold

logger = logging.getLogger(__name__)

# Type alias for the event callback
EventCallback = Callable[[PipelineEvent], Coroutine[Any, Any, None]]


class RecruitPipeline:
    """Orchestrates the full recruitment automation pipeline."""

    def __init__(
        self,
        task_id: int,
        control: TaskControl,
        emit: EventCallback,
    ) -> None:
        self.task_id = task_id
        self.control = control
        self.emit = emit
        self.browser_engine = BrowserEngine()
        self.progress = {
            "searched": 0,
            "pre_matched": 0,
            "greeted": 0,
            "replied": 0,
            "resume_received": 0,
            "scored": 0,
            "qualified": 0,
            "contact_obtained": 0,
        }

    async def run(self) -> None:
        """Execute the full pipeline."""
        db = SessionLocal()
        try:
            task = db.get(RecruitTask, self.task_id)
            if not task:
                raise ValueError(f"Task {self.task_id} not found")

            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()

            position = db.get(Position, task.position_id)
            if not position:
                raise ValueError(f"Position {task.position_id} not found")

            config = json.loads(task.config_json) if task.config_json else {}
            daily_limit = config.get("greeting_daily_limit", 80)
            threshold = config.get("qualified_threshold", get_qualified_threshold())

            await self.emit(PipelineEvent(TASK_STARTED, f"任务启动: {position.title}"))

            # ── Step 1: Position Analysis ──
            await self.emit(PipelineEvent(STEP1_START, "正在分析职位..."))

            jd_data = json.loads(position.jd_json) if position.jd_json != "{}" else None
            if not jd_data:
                analysis = analyze_position(position.title, position.description)
                position.jd_json = json.dumps(analysis.jd.model_dump(), ensure_ascii=False)
                position.keywords_json = json.dumps(
                    {**analysis.keywords.model_dump(), "filters": analysis.filters.model_dump()},
                    ensure_ascii=False,
                )
                position.scorecard_json = json.dumps(analysis.scorecard.model_dump(), ensure_ascii=False)
                db.commit()
                jd_data = analysis.jd.model_dump()

            jd_summary = json.dumps(jd_data, ensure_ascii=False, indent=2)
            keywords_data = json.loads(position.keywords_json)
            scorecard_text = position.scorecard_json

            await self.emit(PipelineEvent(STEP1_DONE, "职位分析完成"))

            # ── Step 2: Launch Browser ──
            await self._check_control()
            await self.emit(PipelineEvent(STEP2_START, "正在启动浏览器..."))

            page = await self.browser_engine.launch()
            if self.browser_engine.context:
                await apply_stealth(self.browser_engine.context)

            await self.emit(PipelineEvent(STEP2_DONE, "浏览器就绪"))

            # ── Step 3: Search & Greet ──
            await self._check_control()
            await self.emit(PipelineEvent(STEP3_SEARCHING, "开始搜索候选人..."))

            search_keywords = keywords_data.get("primary_keywords", [position.title])
            greeting_count = 0

            for keyword in search_keywords:
                if self.control.should_stop or greeting_count >= daily_limit:
                    break

                await navigate_to_search(page)
                await search_candidates(page, keyword)

                # Scan multiple pages of results
                for page_num in range(3):
                    if self.control.should_stop or greeting_count >= daily_limit:
                        break

                    await self._check_control()
                    cards = await get_candidate_cards(page)
                    self.progress["searched"] += len(cards)
                    await self._emit_progress()

                    for card in cards:
                        if self.control.should_stop or greeting_count >= daily_limit:
                            break
                        await self._check_control()

                        # Click to view profile
                        await click_candidate_card(page, card["card_index"])
                        profile = await get_candidate_profile(page)
                        profile_text = json.dumps(profile, ensure_ascii=False)

                        # Pre-match with LLM
                        match_result = pre_match_candidate(jd_summary, profile_text)
                        score = match_result.get("score", 0)
                        self.progress["pre_matched"] += 1

                        # Save candidate to DB
                        candidate = Candidate(
                            task_id=self.task_id,
                            position_id=position.id,
                            name=card.get("name", ""),
                            boss_profile_json=profile_text,
                            pre_match_score=score,
                            status="found",
                        )
                        db.add(candidate)
                        db.commit()
                        db.refresh(candidate)

                        await self.emit(PipelineEvent(
                            STEP3_CANDIDATE_FOUND,
                            f"发现候选人: {card.get('name', '未知')} (初筛: {score}分)",
                            {"candidate_id": candidate.id, "score": score},
                        ))

                        if match_result.get("recommendation") == "建议跳过" or score < 50:
                            candidate.status = "rejected"
                            db.commit()
                            await page.go_back()
                            await random_delay(1, 3)
                            continue

                        # Send greeting
                        greeting = generate_greeting(jd_summary, profile_text)
                        success = await send_greeting(page, greeting)

                        if success:
                            greeting_count += 1
                            candidate.status = "greeted"
                            db.add(ChatMessage(
                                candidate_id=candidate.id,
                                direction="sent",
                                content=greeting,
                                message_type="greeting",
                            ))
                            db.commit()
                            self.progress["greeted"] += 1

                            await self.emit(PipelineEvent(
                                STEP3_GREETING_SENT,
                                f"已打招呼: {card.get('name', '')} ({greeting_count}/{daily_limit})",
                                {"candidate_id": candidate.id, "greeting_count": greeting_count},
                            ))

                        await self._emit_progress()
                        await random_delay(2, 8)

                        # Batch pause
                        throttle = get_config().get("throttle", {})
                        batch_size = throttle.get("batch_pause_count", 12)
                        if greeting_count > 0 and greeting_count % batch_size == 0:
                            pause_min = throttle.get("batch_pause_min", 60)
                            pause_max = throttle.get("batch_pause_max", 180)
                            await self.emit(PipelineEvent(
                                WARNING,
                                f"批次暂停 (已打{greeting_count}个招呼)...",
                            ))
                            await random_delay(pause_min, pause_max)

                        await page.go_back()
                        await random_delay(1, 2)

                    # Scroll to load more
                    await scroll_to_load_more(page)

            # ── Step 3b: Check replies & collect resumes ──
            await self._check_control()
            if not self.control.should_stop:
                await self.emit(PipelineEvent(STEP3_SEARCHING, "检查消息回复..."))
                await self._check_replies(db, page, position, jd_summary, scorecard_text, threshold)

            # ── Complete ──
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.progress_json = json.dumps(self.progress)
            db.commit()

            await self.emit(PipelineEvent(TASK_COMPLETED, "招聘任务完成", self.progress))

        except Exception as exc:
            logger.exception("Pipeline failed for task %d", self.task_id)
            try:
                task = db.get(RecruitTask, self.task_id)
                if task:
                    task.status = "failed"
                    task.error_message = str(exc)
                    db.commit()
            except Exception:
                pass
            await self.emit(PipelineEvent(TASK_FAILED, f"任务失败: {exc}"))
        finally:
            await self.browser_engine.close()
            db.close()

    async def _check_replies(
        self,
        db: Session,
        page: Any,
        position: Position,
        jd_summary: str,
        scorecard_text: str,
        threshold: float,
    ) -> None:
        """Check for candidate replies, collect resumes, score and follow up."""
        from rpa.page_actions import get_unread_messages, navigate_to_chat

        await navigate_to_chat(page)
        conversations = await get_unread_messages(page)

        for conv in conversations:
            if self.control.should_stop:
                break
            await self._check_control()

            # Process each unread conversation
            try:
                element = conv.get("element")
                if element:
                    await element.click()
                    await random_delay(1, 2)

                # Check for resume attachment
                resume_path = await collect_resume(
                    page,
                    conv.get("name", "unknown"),
                    position.title,
                )

                if resume_path:
                    self.progress["resume_received"] += 1

                    # Find the candidate in DB
                    candidate = (
                        db.query(Candidate)
                        .filter(
                            Candidate.task_id == self.task_id,
                            Candidate.name == conv.get("name", ""),
                        )
                        .first()
                    )

                    if candidate:
                        candidate.status = "resume_received"
                        db.commit()

                        await self.emit(PipelineEvent(
                            STEP3_RESUME_RECEIVED,
                            f"收到简历: {candidate.name}",
                            {"candidate_id": candidate.id},
                        ))

                        # ── Step 4: Score the resume ──
                        await self.emit(PipelineEvent(
                            STEP4_SCORING,
                            f"正在评分: {candidate.name}",
                        ))

                        raw_text = parse_resume(resume_path)
                        extracted = extract_resume_info(raw_text)
                        score = score_resume(extracted, jd_summary, scorecard_text)
                        report = generate_report(extracted, score)

                        save_resume_to_db(
                            db=db,
                            candidate_id=candidate.id,
                            file_path=resume_path,
                            file_type=resume_path.split(".")[-1],
                            raw_text=raw_text,
                            extracted_json=extracted.model_dump(),
                            score_json=score.model_dump(),
                            weighted_total=score.weighted_total,
                            is_qualified=score.is_qualified,
                            analysis_report=report,
                        )

                        candidate.status = "scored"
                        self.progress["scored"] += 1
                        db.commit()

                        await self.emit(PipelineEvent(
                            STEP4_SCORED,
                            f"评分完成: {candidate.name} ({score.weighted_total:.1f}分)",
                            {
                                "candidate_id": candidate.id,
                                "score": score.weighted_total,
                                "qualified": score.is_qualified,
                            },
                        ))

                        # ── Step 5: Contact follow-up if qualified ──
                        if score.is_qualified:
                            candidate.status = "qualified"
                            self.progress["qualified"] += 1
                            db.commit()

                            await self.emit(PipelineEvent(
                                STEP5_CONTACT_REQUEST,
                                f"正在索要联系方式: {candidate.name}",
                            ))

                            chat_history = "\n".join(
                                f"{'我' if m.direction == 'sent' else candidate.name}: {m.content}"
                                for m in candidate.messages
                            )

                            contact_msg = generate_contact_request(
                                jd_summary=jd_summary,
                                candidate_profile=candidate.boss_profile_json,
                                chat_history=chat_history,
                                attempt=1,
                            )

                            sent = await send_chat_message(page, contact_msg)
                            if sent:
                                db.add(ChatMessage(
                                    candidate_id=candidate.id,
                                    direction="sent",
                                    content=contact_msg,
                                    message_type="contact_request",
                                ))
                                db.commit()

                await self._emit_progress()
                await random_delay(2, 5)

            except Exception as e:
                logger.error("Error processing conversation: %s", e)
                continue

    async def _check_control(self) -> None:
        """Check if the task is paused or should stop."""
        await self.control.wait_if_paused()
        if self.control.should_stop:
            raise asyncio.CancelledError("Task stopped by user")

    async def _emit_progress(self) -> None:
        """Emit a progress update event."""
        await self.emit(PipelineEvent(
            PROGRESS_UPDATE,
            "进度更新",
            self.progress.copy(),
        ))
