function test_plot() {
	
	var d = new Array();
	var v = 0.0;
	for (i = 0; i < 10000; i++) {
		var x = [v, Math.pow(v, 2.0)];
		d[i] = x;
		v += 1.0 / 1000.0;	
	}
	var x1 = {color: "#000000", data: d, label: "X1", hoverable: true, highlightColor: "#0000ff"};
	
	var data = [ x1 ];
	var options = { 
		series: {
			lines: { show: true },
			points: { show: false }
		},
		xaxis: {
			show: true,
			min: 0.0	,
			max: 5.0
		},
		yaxis: {
			show: true,
			min: 0.0	,
			max: 10.0
		}
	};
	var plot = $("#plot").plot(data, options);	
}


