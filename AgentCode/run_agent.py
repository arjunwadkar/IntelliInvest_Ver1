# run_agent.py
from research_agent import app

if __name__ == "__main__":
    sector_input = input("Enter a sector to analyze: ").strip()
    output = app.invoke({"user_message": sector_input})
    print("\n=== Sector Overview ===\n")
    print(output.get("assistant_response", ""))
    stage = output.get("stage")
    if stage == "subsector_detail":
        subsector_choice = input("\nWhich subsector to deep dive? ")
        output2 = app.invoke({"user_message": subsector_choice, "stage": "subsector_detail"})
        print("\n=== Subsector Deep Dive ===\n")
        print(output2.get("assistant_response", ""))
    else:
        print("\nNo subsectors detected; done.")