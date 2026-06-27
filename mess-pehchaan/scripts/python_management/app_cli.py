import sys
import os

# Ensure config path is set up
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import app_config

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Import module functions
from test.system_health_check import run_health_check
from db.db_seed import seed_database
from db.db_clear import clear_database
from db.db_backup import backup_database
from db.db_restore import restore_database
from logs.export_logs_csv import export_logs_csv
from logs.export_logs_excel import export_logs_excel
from logs.attendance_stats import print_attendance_stats
from logs.visualize_attendance import generate_visualizations
from face_agents.face_recognition_agent import recognize_user
from face_agents.register_face_agent import register_user_with_expressions
from face_agents.expression_invariant_test import test_expression_invariance
from face.batch_register_faces import batch_register

def print_header():
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold amber]MESS PEHCHAAN - SYSTEM MANAGEMENT CONSOLE[/bold amber]\n"
            "[dim]Python Admin Tools & AI Face Recognition Agents[/dim]",
            border_style="amber"
        ))
    else:
        print("=========================================")
        print("    MESS PEHCHAAN - MANAGEMENT CONSOLE   ")
        print("=========================================")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header()
        
        menu_items = [
            ("1", "System Health Check"),
            ("2", "Seed Database with Mock Data"),
            ("3", "Clear Attendance Logs Only"),
            ("4", "Clear All Users & Logs"),
            ("5", "Backup Database to JSON"),
            ("6", "Restore Database from JSON"),
            ("7", "Export Logs to CSV"),
            ("8", "Export Logs to Excel (Pandas)"),
            ("9", "Display Attendance Statistics"),
            ("10", "Generate Visualization Graphs"),
            ("11", "Run AI Face Recognition Agent"),
            ("12", "Register Face AI Agent (Expressions)"),
            ("13", "Run Expression Invariance Test"),
            ("14", "Batch Register Image Directory"),
            ("0", "Exit Console")
        ]
        
        if HAS_RICH:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Option", style="cyan", justify="right")
            table.add_column("Command Description", style="white")
            for opt, desc in menu_items:
                table.add_row(opt, desc)
            console.print(table)
        else:
            for opt, desc in menu_items:
                print(f"  {opt:>2}. {desc}")
            print("-----------------------------------------")
            
        choice = input("\nEnter choice: ").strip()
        
        print("\n" + "-"*40)
        if choice == "1":
            run_health_check()
        elif choice == "2":
            seed_database()
        elif choice == "3":
            clear_database(clear_users=False)
        elif choice == "4":
            confirm = input("Are you sure you want to clear ALL users and logs? (y/N): ")
            if confirm.lower() == 'y':
                clear_database(clear_users=True)
        elif choice == "5":
            out_file = input("Output backup path [database_backup.json]: ").strip()
            out_file = out_file if out_file else "database_backup.json"
            backup_database(out_file)
        elif choice == "6":
            inp_file = input("Input backup path [database_backup.json]: ").strip()
            inp_file = inp_file if inp_file else "database_backup.json"
            restore_database(inp_file)
        elif choice == "7":
            out_file = input("CSV path [attendance_logs.csv]: ").strip()
            out_file = out_file if out_file else "attendance_logs.csv"
            export_logs_csv(out_file)
        elif choice == "8":
            out_file = input("Excel path [attendance_logs.xlsx]: ").strip()
            out_file = out_file if out_file else "attendance_logs.xlsx"
            export_logs_excel(out_file)
        elif choice == "9":
            print_attendance_stats()
        elif choice == "10":
            out_file = input("Chart image path [attendance_analysis.png]: ").strip()
            out_file = out_file if out_file else "attendance_analysis.png"
            generate_visualizations(out_file)
        elif choice == "11":
            img = input("Enter path to face image: ").strip()
            if img:
                recognize_user(img)
        elif choice == "12":
            name = input("Enter student name: ").strip()
            reg = input("Enter registration number: ").strip()
            paths_input = input("Enter image paths separated by commas: ").strip()
            if name and reg and paths_input:
                paths = [p.strip() for p in paths_input.split(',')]
                register_user_with_expressions(name, reg, paths)
        elif choice == "13":
            reg = input("Enter student registration number: ").strip()
            img = input("Enter path to new expression image: ").strip()
            if reg and img:
                test_expression_invariance(reg, img)
        elif choice == "14":
            directory = input("Enter path to images directory: ").strip()
            if directory:
                batch_register(directory)
        elif choice == "0":
            print("Exiting management console. Goodbye!")
            break
        else:
            print("Invalid choice, please select a valid option.")
            
        input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main()
