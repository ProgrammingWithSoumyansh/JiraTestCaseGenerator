import streamlit as st
import openai
import os
import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI

# Streamlit App Title
st.title("Jira Test Case Generator")

# Sidebar for User Inputs
st.sidebar.header("Jira Configuration")
jira_domain = st.sidebar.text_input("Jira Domain (e.g., example.atlassian.net)", "soumyansh.atlassian.net")
issue_key = st.sidebar.text_input("Jira Issue Key", "SCRUM-1")
username = st.sidebar.text_input("Jira Username", "soumyansh@gmail.com")

st.sidebar.header("API Keys")
jira_token_key = st.sidebar.text_input("Jira API Token", type="password")

# Securely fetching OpenAI API Key from Streamlit Secrets
openai_api_key = st.secrets["openai_api_key"]

# OpenAI Client Setup
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

# Function to extract text from Jira's ADF format
def extract_text_from_adf(adf_content):
    """Recursively extracts plain text from Jira's Atlassian Document Format (ADF)."""
    text = ""
    if isinstance(adf_content, list):
        for item in adf_content:
            text += extract_text_from_adf(item) + " "
    elif isinstance(adf_content, dict):
        if "text" in adf_content:
            text += adf_content["text"]
        if "content" in adf_content:
            text += extract_text_from_adf(adf_content["content"])
    return text.strip()

# Function to fetch Jira issue description
def fetch_jira_description(jira_domain, issue_key, username, jira_token_key):
    """Fetches Jira issue description."""
    url = f"https://{jira_domain}/rest/api/3/issue/{issue_key}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers, auth=HTTPBasicAuth(username, jira_token_key))

    if response.status_code == 200:
        issue_data = response.json()
        description_field = issue_data.get("fields", {}).get("description", {}).get("content", [])
        return extract_text_from_adf(description_field) if description_field else "No description found."
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to generate test cases using OpenAI
def generate_test_cases(requirement):
    """Generates test cases using OpenAI."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant capable of generating software test cases in a structured format."},
            {"role": "user", "content": f"Generate well-structured test cases for the following requirement:\n{requirement}\nFormat them like:\nTest Case 1:\n**Scenario:** [Scenario Name]\n**Steps to Reproduce:**\n1. [Step 1]\n2. [Step 2]\n**Expected Result:** [Expected Outcome]"}
        ]
    )
    return response.choices[0].message.content

# Initialize session state variables
if "full_description" not in st.session_state:
    st.session_state.full_description = ""

if "requirement_input" not in st.session_state:
    st.session_state.requirement_input = ""

# Fetch Jira Description on Button Click
if st.button("Fetch Jira Description"):
    if jira_domain and issue_key and username and jira_token_key:
        st.session_state.full_description = fetch_jira_description(jira_domain, issue_key, username, jira_token_key)
        st.session_state.requirement_input = st.session_state.full_description  # Sync text area with fetched data
    else:
        st.error("Please enter all Jira credentials.")

# Requirement Input Box (Linked to Session State)
requirement = st.text_area("Requirement Description", value=st.session_state.requirement_input, key="requirement_input", height=200)

# Generate Test Cases Button
if st.button("Generate Test Cases"):
    if openai_api_key and requirement.strip():
        test_cases = generate_test_cases(requirement)

        # Displaying Test Cases in a More Structured Format
        st.subheader("Generated Test Cases")
        test_cases_list = test_cases.split("\n\n")  # Splitting test cases based on newlines

        for index, test_case in enumerate(test_cases_list, start=1):
            with st.expander(f"Test Case {index}"):
                formatted_case = (
                    test_case.replace("Test Case", "**Test Case**")
                    .replace("Scenario:", "**Scenario:**")
                    .replace("Steps to Reproduce:", "**Steps to Reproduce:**")
                    .replace("Expected Result:", "**Expected Result:**")
                )
                st.markdown(formatted_case)
    else:
        st.error("Please enter a requirement description to generate test cases.")
