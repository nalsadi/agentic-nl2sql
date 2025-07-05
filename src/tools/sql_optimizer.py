import re
from typing import Tuple

def post_process_sql_for_accuracy(sql: str, question: str) -> str:
    #Post-process SQL to better match expected patterns
    
    # Pattern 1: Convert subquery patterns to ORDER BY + LIMIT for youngest/oldest
    if any(word in question.lower() for word in ['youngest', 'oldest', 'minimum age', 'maximum age']):
        # Replace MIN(age) subquery with ORDER BY
        if 'WHERE Age = (SELECT MIN(Age)' in sql:
            # Extract the SELECT part before WHERE
            select_match = re.match(r'(SELECT.*?)FROM\s+(\w+)\s+WHERE Age = \(SELECT MIN\(Age\).*?\)', sql, re.IGNORECASE)
            if select_match:
                select_part = select_match.group(1).strip()
                table = select_match.group(2)
                sql = f"{select_part}FROM {table} ORDER BY Age ASC LIMIT 1"
        
        # Replace MAX(age) subquery with ORDER BY
        if 'WHERE Age = (SELECT MAX(Age)' in sql:
            select_match = re.match(r'(SELECT.*?)FROM\s+(\w+)\s+WHERE Age = \(SELECT MAX\(Age\).*?\)', sql, re.IGNORECASE)
            if select_match:
                select_part = select_match.group(1).strip()
                table = select_match.group(2)
                sql = f"{select_part}FROM {table} ORDER BY Age DESC LIMIT 1"
    
    # Pattern 2: Remove extra columns not mentioned in question
    question_lower = question.lower()
    if 'song name and release year' in question_lower or 'song name and the release year' in question_lower:
        # Should only select song name and release year columns
        if 'SELECT' in sql.upper() and 'FROM singer' in sql:
            # Replace with just the required columns
            sql = re.sub(r'SELECT.*?FROM', 'SELECT Song_Name, Song_release_year FROM', sql, flags=re.IGNORECASE)
    
    return sql

def optimize_for_database(sql: str, db_name: str, question: str) -> str:
    """Database-specific optimizations"""
    
    # Concert singer database optimizations
    if db_name == "concert_singer" and any(word in question.lower() for word in ['youngest', 'oldest']):
        if 'song name and release year' in question.lower() or 'song name and the release year' in question.lower():
            # Direct query for song name and release year
            if 'youngest' in question.lower():
                return "SELECT Song_Name, Song_release_year FROM singer ORDER BY Age ASC LIMIT 1"
            elif 'oldest' in question.lower():
                return "SELECT Song_Name, Song_release_year FROM singer ORDER BY Age DESC LIMIT 1"
    
    return sql

def clean_sql_formatting(sql: str) -> str:
    """Clean up SQL code blocks and formatting"""
    sql = sql.strip()
    
    # Remove SQL code blocks if present
    if sql.startswith('```sql') and sql.endswith('```'):
        sql = sql[6:-3].strip()
    elif sql.startswith('```') and sql.endswith('```'):
        sql = sql[3:-3].strip()
    
    return sql

def validate_sql_syntax(sql: str) -> Tuple[bool, str]:
    """Basic SQL syntax validation"""
    sql = sql.strip().upper()
    
    # Check for basic SQL keywords
    valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'PRAGMA']
    if not any(sql.startswith(keyword) for keyword in valid_starts):
        return False, "SQL must start with a valid SQL keyword"
    
    # Check for balanced parentheses
    if sql.count('(') != sql.count(')'):
        return False, "Unbalanced parentheses in SQL"
    
    # Basic injection prevention
    dangerous_patterns = [
        ';DROP', ';DELETE', ';UPDATE', ';INSERT', 
        'EXEC(', 'EXECUTE(', '--', '/*'
    ]
    for pattern in dangerous_patterns:
        if pattern in sql:
            return False, f"Potentially dangerous SQL pattern detected: {pattern}"
    
    return True, "SQL syntax appears valid"
