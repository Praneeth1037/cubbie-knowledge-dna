"""Deterministic numerical and conservative rubric scoring; never execute student text."""
import re
try:
    from .legacy_diagnose import parse_answer, equivalent
except ImportError:
    from legacy_diagnose import parse_answer, equivalent


def evaluate(question, answer):
    if isinstance(answer, str) and len(answer) > 512:
        raise ValueError("Answers must be at most 512 characters")
    kind = question.get("answer_type", "numeric")
    if kind == "rubric":
        if not isinstance(answer, str):
            return result("ambiguous", "unscored", "Please explain in a short sentence.")
        text = answer.lower()
        if re.search(r"\b(not|never|don't|doesn't|cannot|can't|no)\b", text):
            return result("ambiguous", "unscored", "Please state the operation positively so I can check your meaning.")
        hits = [any(re.search(pattern, text) for pattern in group) for group in question["rubric"]]
        if all(hits):
            return result("correct", "correct", "Your explanation meets the stated rubric.", rubric_hits=hits)
        if any(hits):
            return result("partial", "partial", "Your explanation covers part of the operation.", rubric_hits=hits)
        return result("ambiguous", "unscored", "I cannot establish the required ideas from that wording.", rubric_hits=hits)
    if kind == "dimension" and isinstance(answer, str):
        match = re.match(r"\s*(2|two)\b", answer.lower())
        if match:
            return result("correct", "correct", "You identified the number of components; the reason is not automatically graded.")
    try:
        parsed = parse_answer(answer)
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError, RecursionError):
        return result("ambiguous", "unscored", "I cannot score that format yet; let's use a short focused check.")
    expected = question["expected"]
    if isinstance(expected, list) and not isinstance(parsed, list):
        return result("incomplete", "incomplete", "You sent one number; the requested response contains multiple components.")
    if isinstance(expected, list) and isinstance(parsed, list) and len(parsed) != len(expected):
        return result("incomplete", "incomplete", "The response has a different number of components than requested.")
    if equivalent(parsed, expected, question.get("tolerance", 1e-6)):
        return result("correct", "correct", "That check is correct.")
    for pattern in question.get("patterns", []):
        if equivalent(parsed, pattern["answer"]):
            return result(pattern["tag"], "incorrect", "That response is useful evidence; let's distinguish the possible causes.")
    return result("incorrect", "incorrect", "That check differs from the expected result; one error does not establish its cause.")


def result(signal, verdict, message, **extra):
    return dict(signal=signal, verdict=verdict, message=message, **extra)
