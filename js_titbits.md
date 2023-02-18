# JavaScript titbits

Some small scripts. I had written some more but forgot to save them. I may add more later.

## Add percentage to assignment submissions

While grading submissions using the "Users" tab, assuming you start grading from the top, it shows you your progress by appending the percentages right next to student names. Note that the progress percentage is specific for that page.

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
