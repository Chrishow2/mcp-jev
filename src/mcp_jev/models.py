"""Request validation for Jev tool inputs."""

from __future__ import annotations

from typing import Any

VALID_QUESTION_TYPES = frozenset({"noul", "choice", "score"})
MAX_CHOICE_OPTIONS = 255
MIN_SCORE_LEVELS = 2
MAX_SCORE_LEVELS = 10


class ValidationError(ValueError):
    """Raised when tool inputs fail local validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


def validate_questions(questions: dict[str, Any]) -> None:
    if not isinstance(questions, dict):
        raise ValidationError("questions must be an object")

    if not questions:
        raise ValidationError("questions must not be empty")

    for question_id, question in questions.items():
        if not isinstance(question, dict):
            raise ValidationError(
                f"question '{question_id}' must be an object",
                {"question_id": question_id},
            )

        question_type = question.get("type")
        if question_type not in VALID_QUESTION_TYPES:
            raise ValidationError(
                f"question '{question_id}' has invalid type '{question_type}'",
                {
                    "question_id": question_id,
                    "allowed_types": sorted(VALID_QUESTION_TYPES),
                },
            )

        instructions = question.get("instructions")
        if not isinstance(instructions, str) or not instructions.strip():
            raise ValidationError(
                f"question '{question_id}' requires non-empty instructions",
                {"question_id": question_id},
            )

        criteria = question.get("criteria")
        if question_type == "choice":
            _validate_choice_criteria(question_id, criteria)
        elif question_type == "score":
            _validate_score_criteria(question_id, criteria)
        elif question_type == "noul" and criteria is not None:
            _validate_noul_criteria(question_id, criteria)


def _validate_choice_criteria(question_id: str, criteria: Any) -> None:
    if not isinstance(criteria, dict) or not criteria:
        raise ValidationError(
            f"question '{question_id}' requires criteria map for choice",
            {"question_id": question_id},
        )

    if len(criteria) > MAX_CHOICE_OPTIONS:
        raise ValidationError(
            f"question '{question_id}' exceeds {MAX_CHOICE_OPTIONS} choice options",
            {"question_id": question_id, "count": len(criteria)},
        )

    for option, description in criteria.items():
        if not isinstance(option, str) or not option.strip():
            raise ValidationError(
                f"question '{question_id}' has invalid choice option key",
                {"question_id": question_id},
            )
        if not isinstance(description, str) or not description.strip():
            raise ValidationError(
                f"question '{question_id}' option '{option}' needs a description",
                {"question_id": question_id, "option": option},
            )


def _validate_score_criteria(question_id: str, criteria: Any) -> None:
    if not isinstance(criteria, list) or not criteria:
        raise ValidationError(
            f"question '{question_id}' requires criteria array for score",
            {"question_id": question_id},
        )

    if not MIN_SCORE_LEVELS <= len(criteria) <= MAX_SCORE_LEVELS:
        raise ValidationError(
            f"question '{question_id}' score levels must be "
            f"{MIN_SCORE_LEVELS}-{MAX_SCORE_LEVELS}",
            {"question_id": question_id, "count": len(criteria)},
        )

    for level in criteria:
        if not isinstance(level, str) or not level.strip():
            raise ValidationError(
                f"question '{question_id}' has invalid score level",
                {"question_id": question_id},
            )


def _validate_noul_criteria(question_id: str, criteria: Any) -> None:
    if not isinstance(criteria, dict):
        raise ValidationError(
            f"question '{question_id}' noul criteria must be an object",
            {"question_id": question_id},
        )

    for key in criteria:
        if key not in {"true", "false"}:
            raise ValidationError(
                f"question '{question_id}' noul criteria keys must be 'true' or 'false'",
                {"question_id": question_id, "invalid_key": key},
            )
