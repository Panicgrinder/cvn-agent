"""
Beispiel für die Verwendung der Konversationszusammenfassung.
"""

from app.utils.summarize import summarize_turn
from app.utils.convlog import create_log_record

def beispiel_zusammenfassung():
    # Beispiel-Nachrichten
    messages = [
        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
        {"role": "user", "content": "Was sind die Hauptmerkmale von Python?"}
    ]
    
    # Beispiel-Antwort
    response = """Python ist eine vielseitige Programmiersprache mit zahlreichen Stärken.
    
Zu den wichtigsten Merkmalen von Python gehören:
1. Einfache Syntax und Lesbarkeit
2. Dynamische Typisierung
3. Große Standardbibliothek
4. Plattformunabhängigkeit
5. Starke Community und umfangreiche Bibliotheken wie NumPy, Pandas und TensorFlow

Wichtig ist, dass Python besonders für Einsteiger geeignet ist, aber dennoch für komplexe Aufgaben verwendet werden kann. Beachte, dass Python im Vergleich zu kompilierten Sprachen wie C++ etwas langsamer sein kann, aber dies wird durch die Entwicklungsgeschwindigkeit oft ausgeglichen."""
    
    # Zusammenfassung erstellen
    summary_data = summarize_turn(messages, response)
    
    print("Zusammenfassung:", summary_data["summary"])
    print("\nSchlüsselpunkte:")
    for i, fact in enumerate(summary_data["keyfacts"], 1):
        print(f"{i}. {fact}")
    
    # Optional: Logeintrag mit Zusammenfassung erstellen
    log_entry = create_log_record(
        messages=messages,
        response=response,
        summary=summary_data["summary"],
        labels={"topic": "programming", "language": "python"}
    )
    
    # Logeintrag speichern (auskommentiert, um nicht versehentlich zu loggen)
    # from app.utils.convlog import log_turn
    # log_turn(log_entry)
    
    print("\nZusammenfassung erstellt und bereit zum Loggen.")
    # Vermeidet Unused-Variable-Warnung im Beispiel
    _ = log_entry

if __name__ == "__main__":
    beispiel_zusammenfassung()