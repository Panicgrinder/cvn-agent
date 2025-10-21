from scripts.run_eval import inject_eval_hint


def test_inject_eval_hint_inserts_before_first_user():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Hi"},
    ]
    terms = ["alpha", "beta"]

    out = inject_eval_hint(messages, terms)

    # Der erste user-Eintrag ist jetzt der Hinweis
    first_user_idx = next(i for i, m in enumerate(out) if m.get("role") == "user")
    assert out[first_user_idx]["content"].startswith("Hinweis (Eval):")
    # Der ursprüngliche erste user ist jetzt an Position first_user_idx+1
    assert out[first_user_idx + 1]["content"] == "Hallo"


def test_inject_eval_hint_is_idempotent_on_retry():
    messages = [
        {"role": "user", "content": "Frage"},
    ]
    terms = ["eins", "zwei"]

    once = inject_eval_hint(messages, terms)
    twice = inject_eval_hint(once, terms)

    # Es bleibt bei genau einem Eval-Hinweis
    hints = [m for m in twice if m.get("role") == "user" and str(m.get("content", "")).startswith("Hinweis (Eval):")]
    assert len(hints) == 1
