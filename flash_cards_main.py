# Flash Cards with Categories

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys
import shutil

# Categories will be loaded from JSON files
categories = {}

# Global state variables
current_question_index = 0
current_category = None

def get_app_directory():
	"""Get the directory where the application is running from"""
	if getattr(sys, 'frozen', False):
		# Running as compiled executable
		return os.path.dirname(sys.executable)
	else:
		# Running as script
		return os.path.dirname(os.path.abspath(__file__))

def get_packs_directory():
	"""Get the directory for storing flash card packs (in AppData for write access)"""
	# Use AppData/Local for user-writable data
	appdata_dir = os.path.join(os.environ['LOCALAPPDATA'], 'FlashCards')
	packs_dir = os.path.join(appdata_dir, 'packs')
	
	# Create the directory if it doesn't exist
	if not os.path.exists(packs_dir):
		os.makedirs(packs_dir)
	
	return packs_dir

def copy_default_pack():
	"""Copy the default example pack to AppData if it doesn't exist"""
	packs_dir = get_packs_directory()
	example_pack_dest = os.path.join(packs_dir, "example_flash_cards.json")
	
	# Only copy if it doesn't already exist
	if not os.path.exists(example_pack_dest):
		# Try to find example pack in the app directory
		app_dir = get_app_directory()
		example_pack_source = os.path.join(app_dir, "example_flash_cards.json")
		
		if os.path.exists(example_pack_source):
			shutil.copy2(example_pack_source, example_pack_dest)

def auto_load_packs():
	"""Automatically load all JSON files from the 'packs' folder"""
	packs_dir = get_packs_directory()
	
	# Load all JSON files in the packs directory
	loaded_count = 0
	for filename in os.listdir(packs_dir):
		if filename.endswith('.json'):
			file_path = os.path.join(packs_dir, filename)
			try:
				with open(file_path, 'r') as f:
					imported_categories = json.load(f)
				
				# Add imported categories to existing categories
				for category_name, questions in imported_categories.items():
					categories[category_name] = questions
					loaded_count += 1
			except Exception as e:
				print(f"Error loading {filename}: {e}")
	
	return loaded_count

def open_packs_folder():
	"""Open the packs folder in file explorer"""
	packs_dir = get_packs_directory()
	os.startfile(packs_dir)

def import_pack():
	"""Import flash cards from a JSON file by copying it to the packs folder"""
	try:
		file_path = filedialog.askopenfilename(
			title="Select Flash Cards Pack",
			filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
		)
		
		if not file_path:
			return
		
		# Validate the JSON file first
		try:
			with open(file_path, 'r') as f:
				imported_categories = json.load(f)
		except Exception as e:
			messagebox.showerror("Error", f"Invalid JSON file: {e}")
			return
		
		# Get the packs directory (in AppData)
		packs_dir = get_packs_directory()
		
		# Get the filename from the source path
		filename = os.path.basename(file_path)
		destination = os.path.join(packs_dir, filename)
		
		# Copy the file to the packs folder
		shutil.copy2(file_path, destination)
		
		# Add imported categories to existing categories
		for category_name, questions in imported_categories.items():
			categories[category_name] = questions
		
		# Update the dropdown menu
		update_category_dropdown()
		
		messagebox.showinfo("Success", f"Imported {len(imported_categories)} category/categories!\n\nFile saved to:\n{destination}")
	except Exception as e:
		messagebox.showerror("Import Error", f"An error occurred while importing:\n{str(e)}")

def update_category_dropdown():
	"""Update the category dropdown with current categories"""
	category_var = widgets["category_var"]
	category_dropdown = widgets["category_dropdown"]
	
	# Get current categories
	category_list = sorted(categories.keys())
	
	# Clear and update the dropdown
	menu = category_dropdown["menu"]
	menu.delete(0, "end")
	
	for cat in category_list:
		menu.add_command(label=cat, command=lambda value=cat: category_var.set(value))
	
	# Set default to first category
	if category_list:
		category_var.set(category_list[0])

def submit_category():
	category_var = widgets["category_var"]
	
	choice = category_var.get().strip().lower()
	
	# Start the quiz
	start_quiz(choice)

def submit_answer():
	global current_question_index
	
	answer_entry = widgets["answer_entry"]
	question_label = widgets["question_label"]
	feedback_label = widgets["feedback_label"]

	user_answer = answer_entry.get().strip().lower()
	questions = list(categories[current_category].keys())
	current_question = questions[current_question_index]
	correct_answer = categories[current_category][current_question].lower()
	
	if user_answer == correct_answer:
		# Correct answer - advance to next question or end quiz
		current_question_index += 1
		
		if current_question_index >= len(questions):
			# Quiz completed - show category selection
			start_app()
			return
		else:
			# Move to next question
			next_question = questions[current_question_index]
			question_label.config(text=next_question)
			answer_entry.delete(0, tk.END)
			feedback_label.config(text="Correct! Next question:", fg="green")
			# Auto-focus the answer entry box for the next question
			answer_entry.focus()
	else:
		# Wrong answer - show feedback
		feedback_label.config(text="Incorrect! Try again.", fg="red")

def start_quiz(category):
	global current_category, current_question_index
	
	main_container = widgets["main_container"]
	quiz_container = widgets["quiz_container"]
	question_label = widgets["question_label"]
	answer_entry = widgets["answer_entry"]
	feedback_label = widgets["feedback_label"]

	# Hide main container and show quiz container
	main_container.pack_forget()
	quiz_container.pack(fill="both", expand=True)
	
	# Initialize quiz tracking variables
	current_category = category
	current_question_index = 0
	
	# Update the question for the selected category
	questions = list(categories[category].keys())
	first_question = questions[0]
	question_label.config(text=first_question)
	answer_entry.delete(0, tk.END)
	feedback_label.config(text="")
	# Auto-focus the answer entry box
	answer_entry.focus()

def create_main_container():
	main_container = tk.Frame(root)
	
	# Create a centered frame with max width for fullscreen friendliness
	center_frame = tk.Frame(main_container)
	center_frame.place(relx=0.5, rely=0.5, anchor="center")
	
	tk.Label(center_frame, text="Welcome to Flash Cards!", font=("Arial", 24, "bold")).pack(pady=20)
	tk.Label(center_frame, text="Pick a category:", font=("Arial", 16)).pack(pady=15)
	
	# Create dropdown for category selection
	category_var = tk.StringVar(root)
	# Will be populated after loading packs
	category_dropdown = tk.OptionMenu(center_frame, category_var, "")
	category_dropdown.config(font=("Arial", 14), width=25)
	category_dropdown.pack(pady=15)
	
	tk.Button(center_frame, text="Submit", command=submit_category, font=("Arial", 14), width=25, height=2).pack(pady=10)
	
	# Add import button
	tk.Button(center_frame, text="Import Pack", command=import_pack, bg="#4CAF50", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=10)
	
	# Add button to open packs folder
	tk.Button(center_frame, text="Open Packs Folder", command=open_packs_folder, bg="#2196F3", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=10)
	
	return main_container, category_var, category_dropdown

def create_quiz_container():
	quiz_container = tk.Frame(root)
	
	# Create a centered frame with max width for fullscreen friendliness
	center_frame = tk.Frame(quiz_container)
	center_frame.place(relx=0.5, rely=0.5, anchor="center")
	
	# Display the question
	question_label = tk.Label(center_frame, font=("Arial", 20, "bold"), wraplength=700, justify="center")
	question_label.pack(pady=30)
	
	# Create input box for answer with fixed width
	answer_entry = tk.Entry(center_frame, font=("Arial", 16), width=40, justify="center")
	answer_entry.pack(pady=20)
	answer_entry.bind('<Return>', lambda event: submit_answer())
	
	# Create submit button
	submit_button = tk.Button(center_frame, text="Submit", command=submit_answer, font=("Arial", 14), width=20, height=2, bg="#4CAF50", fg="white")
	submit_button.pack(pady=20)
	
	# Create feedback label
	feedback_label = tk.Label(center_frame, text="", font=("Arial", 14))
	feedback_label.pack(pady=15)
	
	# Create back button
	back_button = tk.Button(center_frame, text="Back to Categories", command=start_app, font=("Arial", 12), width=20)
	back_button.pack(pady=15)
	
	return quiz_container, question_label, answer_entry, submit_button, back_button, feedback_label

def start_app():
	widgets["main_container"].pack(fill="both", expand=True)
	widgets["quiz_container"].pack_forget()

def create_widgets():
	# Create the main container
	main_container, category_var, category_dropdown = create_main_container()

	# Create the quiz container
	quiz_container, question_label, answer_entry, submit_button, back_button, feedback_label = create_quiz_container()

	widgets = {
		"quiz_container": quiz_container, 
		"main_container": main_container,
		"category_var": category_var, 
		"category_dropdown": category_dropdown, 
		"question_label": question_label, 
		"answer_entry": answer_entry, 
		"submit_button": submit_button, 
		"back_button": back_button, 
		"feedback_label": feedback_label,
	}

	return widgets

# Create the main window
root = tk.Tk()
root.title("Flash Cards")

# Start maximized (not fullscreen - keeps title bar and window controls)
root.state('zoomed')

# Create widgets first
widgets = create_widgets()

# Copy default pack to AppData on first run
copy_default_pack()

# Auto-load packs from the 'packs' folder (after widgets are created)
auto_load_packs()
# Update the dropdown to include auto-loaded packs
update_category_dropdown()

# Start app
start_app()

# Start the GUI
root.mainloop()