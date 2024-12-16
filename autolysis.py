import openai
import pandas as pd
from charset_normalizer import detect
import matplotlib.pyplot as plt
import seaborn as sns
import os
import requests
import json
import sys
from dotenv import load_dotenv

load_dotenv()

csv_file = sys.argv[1]
if len(sys.argv) != 2:
    print("Usage: uv run b.py <csv_file>")
    sys.exit(1)

def save_plot(fig, file_name):
    file_path = os.path.join(os.getcwd(), file_name)
    fig.savefig(file_path, bbox_inches="tight")
    plt.close(fig)


def read_dataset(file_path):
 
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = detect(raw_data)
        encoding = result["encoding"]
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        print("File successfully read.")
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    return df
def generate_(file_path):
    directory = str(file_path).split(".")[0]
    if not os.path.exists(directory):
        os.makedirs(directory)
    data = read_dataset(file_path)
    generate_visualizations_in_dir(data, directory)
    narrated_story = generate_story(data)
    create_README(data, directory, narrated_story)




def generate_visualizations_in_dir(data, directory):

    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Correlation heatmap for numerical columns
    numerical_cols = data.select_dtypes(include=["float64", "int64"]).columns
    if len(numerical_cols) > 1:
        plt.figure(figsize=(10, 8))
        correlation_mat = data[numerical_cols].corr()
        sns.heatmap(correlation_mat, annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.savefig(os.path.join(directory, "heatmap.png"))
        plt.close()

    # Distribution plot for the first numerical column
    if len(numerical_cols) > 0:
        plt.figure(figsize=(8, 6))
        sns.histplot(data[numerical_cols[0]], kde=True, color="blue")
        plt.title(f"Distribution of {numerical_cols[0]}")
        plt.savefig(os.path.join(directory, f"distri_{numerical_cols[0]}.png"))
        plt.close()

    # Pairplot for the first few numerical columns (if more than 2 exist)
    if len(numerical_cols) > 2:
        pairplot_data = data[numerical_cols[:4]]  # Limit to the first 4 columns
        sns.pairplot(pairplot_data, diag_kind="kde")
        plt.savefig(os.path.join(directory, "pairplot.png"))
        plt.close()


# readme fn
def create_README(data: pd.DataFrame, directory, narrated_story):
    dataset_path = "dataset_path"
    summary = data.describe(include="all").transpose()
    missing_values = data.isnull().sum()
    with open(f"{directory}/README.md", "w") as f:
        f.write("# Automated Analysis Report\n\n")
        f.write("#Summarized statistical data")

        f.write(f"**Dataset:** `{os.path.basename(dataset_path)}`\n\n")
        f.write("## Summary Statistics\n")
        f.write(narrated_story)
        f.write(summary.to_markdown(tablefmt="github"))
        f.write("\n\n")
        f.write("## Missing Values\n")
        f.write(missing_values.to_markdown(tablefmt="github"))


def generate_story(data):
    token = os.getenv("AIPROXY_TOKEN")
    if token is None:
        print("Error: AIPROXY_TOKEN environment variable not set.")
        sys.exit(1)

    # Generate a summary of the dataset
    columns = data.columns.tolist()
    example_rows = data.head(3).to_dict(orient="records")

    prompt = (
        f"You are a data analyst. Here's a dataset with columns: {columns}.\n\n"
        f"The first three rows are: {example_rows}.\n\n"
        f"Please summarize the dataset, key trends, and any notable patterns or anomalies."
        f"We do not have to describe the meaning of the names of the columns used in the dataset, describe everything statistically."
    )

    # Define the request payload
    api_url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        result = response.json()
        story = result["choices"][0]["message"]["content"]
        return story

    except requests.exceptions.RequestException as e:
        print(f"HTTP request error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error parsing response: {e}")
        sys.exit(1)

generate_(csv_file)