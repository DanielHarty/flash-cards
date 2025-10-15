import streamlit as st
import json
import os
import shutil
import tempfile
from pathlib import Path

# Page configuration
st.set_page_config(
	page_title="Flash Cards v0.0.15",
	page_icon="📚",
	layout="wide",
	initial_sidebar_state="expanded"
)

# Initialize session state
default_state = {
	'categories': {},
	'current_question_index': 0,
	'current_category': None,
	'quiz_started': False,
	'user_answer': "",
	'feedback': "",
	'import_message': None,
	'categories_just_imported': False
}

for key, value in default_state.items():
	if key not in st.session_state:
		st.session_state[key] = value

def get_packs_directory():
	"""Get the directory for storing flash card packs"""
	# Use a local 'packs' directory in the workspace
	packs_dir = Path("packs")
	packs_dir.mkdir(exist_ok=True)
	return str(packs_dir)

def copy_default_pack():
	"""Copy the default example pack to packs folder if it doesn't exist"""
	packs_dir = get_packs_directory()
	example_pack_dest = os.path.join(packs_dir, "example_flash_cards.json")
	
	# Only copy if it doesn't already exist
	if not os.path.exists(example_pack_dest):
		# Try to find example pack in the current directory
		example_pack_source = "example_flash_cards.json"
		
		if os.path.exists(example_pack_source):
			shutil.copy2(example_pack_source, example_pack_dest)

def load_packs():
	"""Load all JSON files from the 'packs' folder"""
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
					st.session_state.categories[category_name] = questions
					loaded_count += 1
			except Exception as e:
				st.error(f"Error loading {filename}: {e}")
	
	
	return loaded_count

def start_quiz(category):
	"""Start a quiz for the selected category"""
	st.session_state.current_category = category
	st.session_state.current_question_index = 0
	st.session_state.quiz_started = True
	st.session_state.user_answer = ""
	st.session_state.feedback = ""

def submit_answer():
	"""Process the user's answer"""
	if not st.session_state.quiz_started or not st.session_state.current_category:
		return False
	
	user_answer = st.session_state.user_answer.strip().lower()
	questions = list(st.session_state.categories[st.session_state.current_category].keys())
	current_question = questions[st.session_state.current_question_index]
	correct_answer = st.session_state.categories[st.session_state.current_category][current_question].lower()
	
	if user_answer == correct_answer:
		# Correct answer - advance to next question or end quiz
		st.session_state.current_question_index += 1
		
		if st.session_state.current_question_index >= len(questions):
			# Quiz completed
			st.session_state.quiz_started = False
			st.session_state.feedback = f"🎉 Quiz completed! You answered all {len(questions)} questions correctly!"
		else:
			# Move to next question
			st.session_state.feedback = "✅ Correct! Next question:"
			st.session_state.user_answer = ""
		return True  # Correct answer, should rerun
	else:
		# Wrong answer - show feedback
		st.session_state.feedback = "❌ Incorrect! Try again."
		return False  # Incorrect answer, no need to rerun

def reset_quiz():
	"""Reset the quiz to the beginning"""
	st.session_state.quiz_started = False
	st.session_state.current_question_index = 0
	st.session_state.current_category = None
	st.session_state.user_answer = ""
	st.session_state.feedback = ""

def main():
	# Load default pack and all packs (only if categories is empty)
	copy_default_pack()
	if not st.session_state.categories:
		load_packs()
	
	# Main title
	st.title("📚 Flash Cards")
	st.markdown("---")
	
	# Sidebar for category selection and controls
	with st.sidebar:
		st.header("📁 Categories")
		
		if st.session_state.categories:
			category_list = sorted(st.session_state.categories.keys())
			
			# Calculate index
			if not st.session_state.quiz_started:
				selected_index = 0
			else:
				if st.session_state.current_category in category_list:
					selected_index = category_list.index(st.session_state.current_category)
				else:
					selected_index = 0
			
			# Category selection
			selected_category = st.selectbox(
				"Choose a category:",
				category_list,
				index=selected_index
			)
			
			# Start quiz button
			if st.button("🚀 Start Quiz", type="primary", use_container_width=True):
				start_quiz(selected_category)
			
			# Reset quiz button
			if st.button("🔄 Reset Quiz", use_container_width=True):
				reset_quiz()
			
			st.markdown("---")
			
			# File upload for importing new packs
			st.header("📥 Import Pack")
			st.info("💡 Uploaded packs are session-only and will be lost when you refresh the page.")
			uploaded_file = st.file_uploader(
				"Upload a JSON flash card pack:",
				type=['json'],
				help="Upload a JSON file with flash card categories and questions"
			)
			
			# Display import message if exists
			if st.session_state.import_message:
				st.success(st.session_state.import_message)
				st.session_state.import_message = None
			
			if uploaded_file is not None:
				# Check if we've already processed this file in this render
				if not st.session_state.categories_just_imported:
					try:
						# Read and validate the JSON
						imported_categories = json.load(uploaded_file)
						
						# Add to existing categories (session-only, not saved to filesystem)
						new_count = 0
						for category_name, questions in imported_categories.items():
							st.session_state.categories[category_name] = questions
							new_count += 1
						
						# Set message for next render
						st.session_state.import_message = f"✅ Imported {new_count} category/categories! (Session only - will be lost on refresh)"
						
						# Set flag and trigger rerun to update dropdown immediately
						st.session_state.categories_just_imported = True
						st.rerun()
						
					except Exception as e:
						st.error(f"❌ Error importing file: {e}")
			else:
				# Reset flag when no file is uploaded
				st.session_state.categories_just_imported = False
			
			# Show pack info
			st.markdown("---")
			st.header("📊 Pack Info")
			for category, questions in st.session_state.categories.items():
				st.write(f"**{category}**: {len(questions)} questions")
			
		else:
			st.warning("No flash card packs found. Please import a JSON file.")
	
	# Main content area
	if st.session_state.quiz_started and st.session_state.current_category:
		# Quiz interface
		questions = list(st.session_state.categories[st.session_state.current_category].keys())
		current_question = questions[st.session_state.current_question_index]
		
		# Progress bar
		progress = (st.session_state.current_question_index + 1) / len(questions)
		st.progress(progress, text=f"Question {st.session_state.current_question_index + 1} of {len(questions)}")
		
		# Question display
		st.markdown(f"### Category: {st.session_state.current_category}")
		st.markdown(f"### Question: {current_question}")
		
		# Answer input with form for Enter key support
		with st.form("answer_form", clear_on_submit=False):
			col1, col2 = st.columns([3, 1])
			
			with col1:
				user_input = st.text_input(
					"Your answer:",
					value=st.session_state.user_answer,
					key="answer_input",
					placeholder="Type your answer here...",
					label_visibility="collapsed"
				)
			
		with col2:
			submitted = st.form_submit_button("Submit", type="primary", use_container_width=True)
		
		if submitted:
			# Update session state with the current input value
			st.session_state.user_answer = user_input
			should_rerun = submit_answer()
			if should_rerun:
				st.rerun()
		
		# Feedback display
		if st.session_state.feedback:
			if "✅" in st.session_state.feedback or "🎉" in st.session_state.feedback:
				st.success(st.session_state.feedback)
			else:
				st.error(st.session_state.feedback)
		
		# Keyboard shortcut info
		st.markdown("💡 **Tip**: Press Enter in the text input to submit your answer!")
		
	else:
		# Welcome screen
		if st.session_state.categories:
			st.markdown("### Welcome to Flash Cards! 🎯")
			st.markdown("Select a category from the sidebar and click 'Start Quiz' to begin.")
			
			# Display available categories
			st.markdown("#### Available Categories:")
			for category, questions in st.session_state.categories.items():
				with st.expander(f"📚 {category} ({len(questions)} questions)"):
					question_list = list(questions.keys())
					for i, question in enumerate(question_list, 1):
						st.write(f"{i}. {question}")
		else:
			st.markdown("### Welcome to Flash Cards! 🎯")
			st.markdown("No flash card packs found. Please upload a JSON file using the sidebar.")
			
			# Show example format
			with st.expander("📝 Example JSON format"):
				st.code('''
{
	"category_name": {
		"Question 1?": "answer1",
		"Question 2?": "answer2"
	}
}
				''', language="json")

if __name__ == "__main__":
	main()
