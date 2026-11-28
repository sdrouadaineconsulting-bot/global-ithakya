<?php
// Usage: php gen_config.php <out> <env:local|production> <json-overrides>
$pw = trim(file_get_contents(__DIR__.'/.dbpw'));
$c = ['enabled'=>true,'environment'=>$argv[2],'origin'=>'https://127.0.0.1:8443',
 'password_pepper'=>str_repeat('a1',48),'bootstrap_invitation'=>str_repeat('b2',32),
 'database'=>['driver'=>'mysql','host'=>'127.0.0.1','name'=>'ithakya_banc','user'=>'ithakya','password'=>$pw],
 'attenzia_agregats'=>true,'attenzia_banc_synthetique'=>true,'attenzia_k'=>5];
$c = array_replace_recursive($c, json_decode($argv[3] ?? '{}', true) ?: []);
file_put_contents($argv[1], "<?php\nreturn ".var_export($c,true).";\n");
