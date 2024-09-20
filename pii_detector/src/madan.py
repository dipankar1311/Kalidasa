import os
import subprocess


pii_time = {
    "start_time": "10",
    "end_time": "10",
}

start = float(pii_time["start_time"])
end = float(pii_time["end_time"])
duration = float(end - start)
input_file = "pii-test-fie1.mp4"
output_file = "pii-test-fie1-processed.mp4"

command = f"""
    ffmpeg -i {input_file} -af "volume=enable='between(t,{start},{end})':volume=0[main];sine=d={duration}:f=800,adelay={start}s,pan=stereo|FL=c0|FR=c0[beep];[main][beep]amix=inputs=2" {output_file}
""".strip()

print(command)

# Execute command on terminal
# os.system(command)

# Execute command on terminal with Popen
process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output, error)
