"""
Test Cycle - Runs one scheduler cycle immediately
"""

from main import AlertScheduler

def main():
    print("🧪 Testing cycle...\n")
    scheduler = AlertScheduler()
    scheduler.run_cycle()
    print("\n✅ Test completed")

if __name__ == "__main__":
    main()
