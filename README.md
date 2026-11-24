# GainCheck

GainCheck tells you whether you are actually getting stronger.

Most training apps record your workouts and show you a chart. A single great day looks like progress, and a stalled lift is easy to miss. GainCheck looks at your logged training, separates real gains from one-off spikes, and writes you a monthly report in plain language.

## What you can do

**Log your training**
- Record workouts as sets of weight and reps for each exercise.
- Pick from a built-in list of common exercises.
- Add a note to any workout, such as "slept badly" or "elbow sore".

**Track your body**
- Log bodyweight and measurements (waist, chest, arm) over time.
- Add notes to explain changes, such as a cut or a bulk.

**See your progress**
- Estimated one-rep max for each lift.
- Personal records for weight, reps and volume.
- Strength relative to your bodyweight.
- A training level for each lift (for example beginner, intermediate, advanced), based on published strength standards for your sex and bodyweight.
- Consistency: how regularly you train.

**Know whether a gain is real**
- A confirmed gain is one that holds up across several sessions.
- A spike is a single strong session that you have not repeated.
- GainCheck tells you how long a lift has been in a plateau.

**Get a monthly report**
- A verdict for each lift: progressing, plateaued or regressing.
- A short written summary of your month.
- Practical suggestions for what to change next.
- Reports account for your profile and goal, so a strength-focused lifter and a fat-loss lifter are judged differently.

**Keep your data private**
- Sign up with email and password.
- You can only see your own workouts, measurements and reports.

## Who it is for

Anyone who lifts regularly and wants an honest answer to "is this working?", from a beginner on their first program to an experienced lifter chasing a plateau.

## Status

Early development. The project structure is in place, and features are being built step by step.

## Project layout

- `backend/` holds the server that stores data and produces the analysis and reports.
- `frontend/` holds the web app you use.
- `docs/` holds design notes.
