<?php
	$key = "CZToGZGv629SDKoFHtBYAPVF";
	require "libs/oaapi.php";

	$oa = new OAAPI($key);

	$func = "getDebates";
	$args = array(
		"type" => "representatives",
		"search" => "marriage",
//	num doesn't seem to be valid
//		"num" => 10,
	);
	print "<pre>";
	print $func;

	print_r($args);
	print "</pre>";
	
	print "<textarea>";
	$results = $oa->query($func, $args);
	print $results;
	print "</textarea>";
	print "OK";
?>
