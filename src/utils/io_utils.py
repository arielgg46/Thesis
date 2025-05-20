import os
import json

def save_text(file_path, content):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def make_case_dir(output_root, agent, domain, idx):
    case_dir = os.path.join(output_root, agent, f"{domain}_{idx}")
    os.makedirs(case_dir, exist_ok=True)
    return case_dir

def load_json_data(file_path):
  """
  Reads a JSON file and loads its content into a Python object.

  Args:
    file_path: The path to the JSON file.

  Returns:
    A Python object representing the JSON data, or None if an error occurs.
  """
  try:
    with open(file_path, 'r') as f:  # Open the file in read mode ('r')
      data = json.load(f)          # Use json.load() to parse the JSON data
    return data                       # Return the loaded object
  except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    return None
  except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in {file_path}")
    return None
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
    return None
  
def save_data_to_json(data, file_path, indent=4):
    """
    Saves a Python object to a JSON file, creating the file if it doesn't exist.

    Args:
        data: The Python object to save.
        file_path: The path to the JSON file.  The entire path, including any directory names, will be created if needed.
        indent: The indentation level for the JSON file (optional, defaults to 4). Use None for no indentation.

    Returns:
        True if the save was successful, False otherwise.
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except TypeError as e:
        print(f"Error: Cannot serialize data to JSON. Check for unsupported data types in the object. Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False