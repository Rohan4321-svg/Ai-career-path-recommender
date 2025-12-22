import streamlit as st
import pandas as pd
import re
import openai
import os

# -------------------------------
# Load CSV and clean skills
# -------------------------------
CSV_PATH = r'C:\Users\Rohann\Downloads\project\jobs_skills_mapping.csv'
df = pd.read_csv(CSV_PATH)

def clean_skills(skills_str):
    if pd.isna(skills_str):
        return []
    skills_str = re.sub(r"[\[\]']", '', skills_str)
    skills_list = [skill.strip().lower() for skill in skills_str.split() if skill.strip()]
    return skills_list

df['Skills_required'] = df['Skills_required'].apply(clean_skills)
df.dropna(subset=['job_title'], inplace=True)
df = df[df['Skills_required'].map(len) > 0].reset_index(drop=True)

# -------------------------------
# Matching function
# -------------------------------
def match_careers(user_skills, df, top_n=5):
    user_skills = [skill.lower().strip() for skill in user_skills]

    def count_matches(job_skills):
        count = 0
        for u_skill in user_skills:
            for j_skill in job_skills:
                if u_skill in j_skill or j_skill in u_skill:
                    count += 1
        return count

    df['match_count'] = df['Skills_required'].apply(count_matches)
    matched = df[df['match_count'] > 0].sort_values(by='match_count', ascending=False)
    return matched[['job_title', 'Skills_required', 'Industry', 'Pay_grade', 'match_count']].head(top_n)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("AI-Based Career Path Recommender")

user_input = st.text_input(
    "Enter your skills separated by commas (e.g., python, sql, communication):"
)

if st.button("Get Career Recommendations") and user_input:
    user_skills = [skill.strip() for skill in user_input.split(',')]
    
    # Match careers
    top_matches = match_careers(user_skills, df)
    
    if top_matches.empty:
        st.warning("No matching careers found. Try adding more skills.")
    else:
        st.subheader("Top Career Matches")
        for _, row in top_matches.iterrows():
            st.markdown(f"**Job Title:** {row['job_title']}")
            st.markdown(f"**Skills Required:** {', '.join(row['Skills_required'])}")
            st.markdown(f"**Industry:** {row['Industry']}")
            st.markdown(f"**Pay Grade:** {row['Pay_grade']}")
            st.markdown(f"**Matched Skills Count:** {row['match_count']}")
            st.markdown("---")
        
        # GPT Integration
        openai.api_key = "your_openai_api_key_here" # or put your key here
        
        prompt = f"You are a career guidance assistant. The user has these skills: {', '.join(user_skills)}.\n"
        prompt += "Top matching jobs:\n"
        for _, row in top_matches.iterrows():
            prompt += f"- {row['job_title']}: requires {', '.join(row['Skills_required'])}, Industry: {row['Industry']}, Pay Grade: {row['Pay_grade']}\n"
        prompt += "\nProvide personalized career guidance and advice to improve skills."
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert career advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        st.subheader("GPT Personalized Career Advice")
        st.write(response.choices[0].message.content)

