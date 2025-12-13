# Computeranwendungen in der Physik: Grundlagen der Programmierung in Python

**Interal** repository for the teachers: Notebooks and other materials, possibly including solutions.


## Setup

Everything should run on the [PHYSnet JupyterHub server](https://jhub.physnet.uni-hamburg.de/) to achieve a consistent setup with the students.

- After login (single-thread setup should suffice), start a new Terminal from the Launcher
- Clone this repository at the desired location, e.g.,
  ```bash
  mkdir computeranwendungen-in-der-physik
  cd computeranwendungen-in-der-physik
  git clone https://git.physnet.uni-hamburg.de/computeranwendungen-in-der-physik/grundlagen-material.git
  # or:
  # git clone git@git.physnet.uni-hamburg.de:computeranwendungen-in-der-physik/grundlagen-material.git
  ```
- In the file browser panel (left), look for the file [`00_setup.ipynb`](00_setup.ipynb) (e.g., in `computeranwendungen-in-der-physik/grundlagen-material`) and open it
- Choose the right kernel (descriped at the top of the file) and execute all cells. **This step is needed exactly once before creating or executing any other notebook!**


# Creating Exercises / Problems
To create an exercise that can be auto-graded you have to follow one of the prepared patterns that are described in  
[tests/01_example_problems.ipynb](tests/01_example_problems.ipynb).  
For the students a stripped version will be generated like this one  
[tests/01_example_problems_student_version.ipynb](tests/01_example_problems_student_version.ipynb).  
(Also, cell tags and metadata are set.)

The CI takes care of creating the stripped notebooks. You can check the [pipelines](https://git.physnet.uni-hamburg.de/computeranwendungen-in-der-physik/grundlagen-material/-/pipelines). If they succeed for your push, you can
- click the second green checkmark
- click generate-student-versions
- on the right side bar "Job artifacts", click "Browse"


# Live Demos
If you want to create a live demo that the tutor can solve together with the students (no graded assigment!), you can use the comment lines
```python
def f(n):
# BEGIN-LIVE
    """
    sample-code for the tutors to look at
    which will be stripped for the student version
    to perform a live demo together
    """
# END-LIVE

f(1), f(2), f(3)
```

# Singularity / docker for grading

**Do not** simply run batch grading on your system (laptop, physnet, etc.), because you will blindly run code which is a huge security threat!
Instead, use singularity as described below, properly isolating file systems and disabling network!

## Build

For singularity, build on a machine where you have root access via

```
sudo singularity build singularity/python3.9.2.sif singularity/python3.9.2.def
# make it usable by yourself
sudo chown $USER:$USER singularity/python3.9.2.sif
```

For docker, run

```shell
docker build -t python_abk -f singularity/Dockerfile .
```

in the repository root directory.

## Run

Run from the base directory of this repository. At the moment you have to edit the paths in these shells scripts that control what is mounted etc.:
```
./util/run_batch_grading.sh
# or
./util/run_single_nb_grading.sh
```
