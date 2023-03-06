# JavaScript titbits

Some small scripts. I had written some more but forgot to save them. I may add more later.

## Add percentage to assignment submissions

While grading submissions using the "Users" tab, assuming you start grading from the top, it shows you your progress by appending the indices and percentages right next to student names. Note that the progress is specific to that page.

```JavaScript
let count = $('td.dlay_l').size();

function round_precised(number, precision) {
	var power = Math.pow(10, precision);
	return Math.round(number * power) * 100 / power;
}

$('td.dlay_l').each(function(index, element) {
	let percentage = round_precised((index+1)/count, 3);
	$('td.dlay_l')[index].append(" ("+(index+1)+" of "+count+", "+percentage+"%)");
});
```

## Distribute student submissions

This function distributes the submissions among TAs based on their required workload weight. Note that the distribution is page-wise. If there are more than 200 students, it would not be possible to display and assign all of them together. To assign only students with submissions, you need to filter them before you run the function. If there are remaining students who were not assigned to anyone, they are printed as well.

```JavaScript
function distribute_submissions(ta_weights){
	let submissions = document.querySelectorAll("td.dlay_l > a");
	let submission_counter = 0;

	// Prints each TAs assigned student range.
	Object.keys(ta_weights).forEach(function(ta){ 
		if (submission_counter >= submissions.length){
			console.log("No submission left for " + ta);
			return;
		}
		weight = ta_weights[ta];
		if (weight < 1){
			console.log("Invalid weight for " + ta);
			return;
		}
		let grade_until = submission_counter + weight;
		let students = [];
		let first = submissions[submission_counter].innerText;
		while (submission_counter < grade_until && submission_counter < submissions.length){
			students.push(submissions[submission_counter].innerText);
			submission_counter += 1;
		}
		let last = submissions[submission_counter-1].innerText;
		console.log(ta + ": " + students.length + " students between " + first + " and " + last);
	});

	// Prints the remaining students if there are more than assigned.
	if (submission_counter < submissions.length){
		console.log("WARNING! The following submissions are not assigned to anyone:");
		for (let i = submission_counter; submission_counter < submissions.length; i++){
			console.log(submissions[i].innerText);	
		}
	}
}

distribute_submissions({"TA 1": 10, "TA 2": 20, "TA 3": 30});
```
