"""
try_it.py - choose a location, type the emergency message, see the volunteers.

Run:  python try_it.py
  Step 1: type the NUMBER of the location (the drop-down list)
  Step 2: type the emergency message (the text box)
  Type  location  to change the location,  quit  to stop.
"""
from hub_pipeline import show, CITIES

EXAMPLES = [
    "there is a medical emergency need volunteers",
    "there is a flood",
    "need food packets, no hurry",
    "ambulance needed immediately, road accident",
]


def choose_city():
    print("\nChoose the location:")
    for i, c in enumerate(CITIES, start=1):
        print(f"  {i}. {c}")
    while True:
        choice = input("Location number> ").strip()
        if choice.lower() in ("quit", "exit", "q"):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(CITIES):
            return CITIES[int(choice) - 1]
        print(f"Please type a number from 1 to {len(CITIES)}.")


print("Community Disaster Volunteer Hub - message tester")
print("Examples of messages you can type:")
for e in EXAMPLES:
    print("  ", e)

city = choose_city()
while city is not None:
    print(f"\nLocation: {city}   (type 'location' to change, 'quit' to stop)")
    try:
        text = input("Emergency message> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if text.lower() in ("quit", "exit", "q"):
        break
    if text.lower() == "location":
        city = choose_city()
        continue
    if not text:
        print("Please type a message first.")
        continue
    show(text, city)

print("Goodbye!")