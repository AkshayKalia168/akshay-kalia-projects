# akshay-kalia-projects
A collection of personal and academic projects written in C and Python, showcasing foundational programming skills and problem-solving.

---

### 🏭 ScrapSense (Manufacturing Scrap Logging App) – Python + Tkinter

**ScrapSense** is a full-featured desktop application built with Python and Tkinter that allows manufacturing teams to log, track, and analyze production scrap.  
It integrates real-time dashboards, data visualization, and predictive analytics, designed for easy use in factory and industrial environments.

This project demonstrates advanced Python concepts including:
- Object-Oriented GUI design using **Tkinter**  
- **SQLite/PostgreSQL** database integration  
- Data visualization with **Matplotlib** and **Plotly**  
- Report generation with **Jinja2** and **pdfkit**  
- Modular multi-frame architecture for navigation between pages  

---

#### 💡 Core Features:
- 📊 **Dashboard:** Displays KPIs like total scrap, cost, and top causes  
- ➕ **Add Scrap:** Log new scrap entries with operator, machine, reason, and shift details  
- 📁 **View Logs:** Filter scrap history by operator, date, or shift  
- 🤖 **View Predictions:** Analyze predicted monthly scrap using regression models  
- 📑 **Generate Report:** Export analytics and charts into professional PDF reports  

---

#### 🧠 Key Technical Highlights:
- Multi-page Tkinter interface with persistent sidebar navigation  
- Responsive layout that adapts to different screen resolutions  
- Real-time clock and dynamic KPI updates  
- PDF report generation (PowerBI-style) with embedded charts  
- Designed for manufacturing efficiency and recruiter showcase  

---

#### 🖼️ Example Screenshot:
*(Dashboard view – showing KPIs and navigation sidebar)*  
![ScrapSense Dashboard](images/dashboard_example.png)

---

#### ▶️ How to Run:
```bash```
pip install -r requirements.txt
python3 main.py


### 🧼 CSV Cleaner (`csv_cleaner.py`) – Python

This Python script reformats a CSV file by splitting full names into separate `first` and `last` columns and preserving the `department` field. It reads an input CSV file (with a "name" and "department" column) and writes a new CSV file in a clean, structured format.

It's useful for:
- Practicing file input/output and CSV parsing in Python
- Learning how to use the `csv.DictReader` and `csv.DictWriter` modules
- Gaining experience with command-line arguments and data cleaning

#### 💡 How It Works:
– The user provides two command-line arguments: the input CSV file and the output CSV file.  
– Each row in the input file has a `"name"` column (in `"Last, First"` format) and a `"department"` column.  
– The script splits the name, cleans the data, and writes it in the format: `first`, `last`, `department`.

This project demonstrates core Python concepts like:
– File input/output  
– Dictionary manipulation  
– Error handling and command-line validation  
– CSV parsing using the built-in `csv` module  

#### 🔍 Example:

Input (`before.csv`):
```csv
name,department  
"Smith, John",Engineering  
"Doe, Jane",Marketing  
"Johnson, Emily",Human Resources  

Output (`after.csv`):
first,last,department  
John,Smith,Engineering  
Jane,Doe,Marketing  
Emily,Johnson,Human Resources  
```

### 🎮 Wordle Game Clone (`wordle.c`) - C

A terminal-based version of the Wordle game written in C. This game reads a secret 5-letter word from a file and allows the user up to 6 attempts to guess it. Letters that are correct and in the correct position are shown in uppercase. Correct letters in the wrong position are marked with `^` symbols underneath.

This project showcases skills in:
- C programming fundamentals
- File input/output (`fopen`, `fscanf`)
- Arrays and string manipulation
- ASCII operations and lowercase conversion
- Game loop control and win/loss logic
- User input validation and feedback

---

#### 💡 How It Works:
- Reads a 5-letter mystery word from `mystery.txt`
- Prompts the user up to 6 times to guess the word
- Each guess is validated for length and character type
- Feedback is given after each guess:
  - Correct letter & correct position → **Capitalized**
  - Correct letter & wrong position → **Marked with `^`**
- The game ends on a correct guess or after 6 attempts

---

#### 🛠️ Features:
- Case-insensitive input handling
- ASCII manipulation to handle uppercase/lowercase logic
- Input validation for word length and non-alphabetic characters
- Simple visual feedback using `^` markers
- Modular function design (validation, feedback, win check, etc.)

---

#### 🧪 Example Gameplay:

```text
GUESS 1! Enter your guess: light
LIGHT
 ^  ^

GUESS 2! Enter your guess: blunt
BLUNT
 ^ ^

FINAL GUESS: crate
CRATE
^^ ^

You lost, better luck next time!
```

✅ If you win:
```text
GUESS 2! Enter your guess: place
PLACE
^ ^^
You won in 2 guesses!
                Amazing!
```

---

#### ▶️ How to Compile and Run:
1. Save a 5-letter word (e.g., `apple`) in a file called `mystery.txt`
2. Compile:
```bash
gcc -o wordle wordle.c
```
3. Run:
```bash
./wordle
```




