# Open a jsonl file and remove all the json objects that have a where "problem_id" key matches with the given list of problem_ids
import json

def remove_problem_ids_from_jsonl(jsonl_file, problem_ids):
    # Create a new file to store the filtered data
    new_jsonl_file = jsonl_file.replace('.jsonl', '_filtered.jsonl')
    
    with open(jsonl_file, 'r') as f:
        with open(new_jsonl_file, 'w') as new_f:
            for line in f:
                data = json.loads(line)
                # if data['problem_id'] not in problem_ids: #or data['is_proven']:
                if not data['is_proven']:
                    new_f.write(line)
    
    # # Replace the original file with the new file
    # os.remove(jsonl_file)
    # os.rename(new_jsonl_file, jsonl_file)

if __name__ == "__main__":
    problem_ids = [
    ]
    path = "/home/amthakur/Project/clever-prover/.logs/checkpoints/few_shot_impl_copra_proof.jsonl"
    remove_problem_ids_from_jsonl(path, problem_ids)