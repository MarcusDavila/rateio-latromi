# Rateio Importer - Freight Cost Allocation System

A web application developed in Python/Flask to automate the allocation of entry invoice costs by linking them to Transport Documents (CRT/CTE) listed in Excel or CSV spreadsheets.

## 🚀 Features

1.  **Invoice Search**: Locate entry invoices using the Supplier's CNPJ and Invoice Number.
2.  **Smart File Processing**:
    *   Support for Excel (`.xlsx`, `.xls`) and CSV formats.
    *   Automatic scanning of **all tabs** within Excel files.
    *   Automatic identification of transport document columns (searching for names like CRT, CTE, CONHECIMENTO).
    *   **Data Cleaning**: Uses Regex to normalize document numbers (e.g., removing leading prefixes).
3.  **Data Validation**: Verifies transport documents against the database before processing.
4.  **Review Interface**: A detailed table to audit identified documents and manually adjust allocation values.
5.  **Secure Persistence**: Batch insertion into the system database with currency formatting and integrity checks.

## 🛠️ Tech Stack

*   **Backend**: Python 3, Flask.
*   **Database**: PostgreSQL (`psycopg2`).
*   **Data Handling**: Pandas, OpenPyXL.
*   **Frontend**: HTML5, CSS3 (Custom Premium Theme), Bootstrap 5.

## 📂 Project Structure

The project follows a modular architecture for better maintainability:

*   `app.py`: Main controller handling routes and application logic.
*   `services.py`: Business logic, including file parsing and allocation calculations.
*   `database.py`: Database connection management and pool handling.
*   `queries.py`: Centralized SQL query constants.
*   `static/css/styles.css`: Custom premium styling with "Indigo & Slate" palette and glassmorphism elements.

## ⚙️ Installation & Setup

### 1. Requirements
*   Python 3.10+
*   PostgreSQL Database

### 2. Setup
```bash
# Clone the repository
git clone https://your-repository-url.git
cd rateio-latromi

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
DB_HOST=your_host
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432
SECRET_KEY=your_flask_secret_key
```

## 🌐 Network Access

The application is configured to be accessible on your local network (LAN). 

1.  Run the application: `python app.py`
2.  Find your computer's IP address (e.g., `192.168.1.5`).
3.  Access from another device: `http://192.168.1.5:5000`

> [!NOTE]
> Ensure port `5000` is open in your Windows Firewall settings.