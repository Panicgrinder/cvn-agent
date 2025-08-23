"""
Dokumentation für die Anpassung des CVN Agents an Ihre persönlichen Anforderungen

Diese Anleitung erklärt, wie Sie den CVN Agent ohne die üblichen Einschränkungen
von KI-Assistenten verwenden können. Sie haben volle Kontrolle über den Inhalt und
die Regeln, die in Ihrer privaten Installation des Agents gelten.
"""

# Übersicht

Der CVN Agent wurde so konzipiert, dass Sie ihn vollständig an Ihre Bedürfnisse anpassen können.
Als privater Benutzer haben Sie die Möglichkeit, Einschränkungen zu entfernen und den
Agent genau so zu konfigurieren, wie Sie es für Ihre Zwecke benötigen.

## Verfügbare Modi

Der CVN Agent unterstützt drei verschiedene Modi:

1. **Standard-Modus**: Rollenspiel als Chronistin von Novapolis mit allgemeinen Inhalten
2. **Evaluierungs-Modus**: Sachliche Antworten ohne Rollenspiel (für Tests)
3. **Uneingeschränkter Modus**: Vollständig anpassbarer Modus ohne externe Filterung

## Anpassung des uneingeschränkten Modus

Um den CVN Agent ohne Einschränkungen zu verwenden, können Sie:

1. Den uneingeschränkten Prompt anpassen:
   ```
   python scripts/customize_prompts.py --customize-unrestricted
   ```

2. Eigene Regeln definieren:
   ```
   python scripts/customize_prompts.py --create-rules
   ```

3. Den uneingeschränkten Modus beim Aufruf aktivieren:
   ```
   curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Deine Anfrage"}],"unrestricted_mode":true}'
   ```

## Wichtige Dateien für die Anpassung

- `app/core/prompts.py`: Enthält alle System-Prompts
- `app/core/content_management.py`: Verwaltet Inhaltsfilter
- `examples/unrestricted_prompt_example.txt`: Beispiel für einen uneingeschränkten Prompt

## Datenschutz und Verantwortung

Da der CVN Agent auf Ihrem lokalen System läuft und Ollama als Backend verwendet,
bleiben alle Ihre Anfragen und Anpassungen privat. Sie allein sind für die Art der
Inhalte verantwortlich, die Sie generieren.

Denken Sie daran, dass der uneingeschränkte Modus vollständig unter Ihrer Kontrolle steht.
Sie können den Systemprompt nach Ihren Vorstellungen gestalten, ohne die Einschränkungen,
die normalerweise bei öffentlichen KI-Diensten gelten würden.

## Beispiel für einen uneingeschränkten Prompt

In der Datei `examples/unrestricted_prompt_example.txt` finden Sie ein Beispiel für
einen uneingeschränkten Prompt, den Sie als Ausgangspunkt verwenden können.