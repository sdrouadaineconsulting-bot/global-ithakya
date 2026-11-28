<?php
declare(strict_types=1);
define('ITP_SCHEMA', 'test_complements');
require $argv[1];
function fail(int $status, string $code, string $message): never {throw new RuntimeException($code, $status);}
function snapshot(array $cell, int $k=5, string $serie='cumul'): array {
    $payload=json_encode(['donnees'=>['univers'=>['mire'=>$cell]]],JSON_THROW_ON_ERROR);
    return ['serie'=>$serie,'payload'=>$payload,'checksum'=>hash('sha256',$payload),'k'=>$k];
}
function guard(array $cell, array $history=[],int $k=5,string $serie='cumul'): array {
    $d=['univers'=>['mire'=>$cell,'independant'=>['participants'=>50]]];
    $n=itpAtzMasquerRecoupements($d,$history,$serie,$k);
    if($d['univers']['independant']['participants']!==50) throw new RuntimeException('Cellule indépendante altérée');
    return ['cellule'=>$d['univers']['mire'],'masques'=>$n];
}
$cases=[];
$a=['participants'=>15,'long_ouverts'=>5];
$b=['participants'=>20,'long_ouverts'=>11];
$c=['participants'=>26,'long_ouverts'=>16];
$first=guard($a);$second=guard($b,[snapshot($first['cellule'])]);$third=guard($c,[snapshot($first['cellule']),snapshot($second['cellule'])]);
$cases['trois_publications']=['premiere'=>$first,'deuxieme'=>$second,'troisieme'=>$third];
$cases['petit_complement_interne']=guard(['participants'=>20,'court_termines'=>15,'long_ouverts'=>11,'long_apres_court'=>10,'taux_approfondissement'=>0.667]);
$cases['historique_inverse']=guard($b,[snapshot(['participants'=>null,'long_ouverts'=>null]),snapshot($a)]);
$cases['seuil_historique_superieur']=guard(['participants'=>25,'long_ouverts'=>9],[snapshot(['participants'=>15,'long_ouverts'=>5],7)]); // direct variation below historical k
$cases['valeur_masquee_non_zero']=guard(['participants'=>20,'long_ouverts'=>null],[snapshot($a)]);
$cases['complements_stables']=guard(['participants'=>25,'long_ouverts'=>15],[snapshot($a)]);
$cases['autre_serie']=guard($b,[snapshot($a,5,'mois')]);
$n=0;$ok=function(bool $v)use(&$n){if(!$v)throw new RuntimeException('Assertion complément '.($n+1));$n++;};
if(in_array(ITP_ATZ_REGLE_INST,['ATZ-INSTANTANES-V3.6','ATZ-INSTANTANES-V3.7','ATZ-INSTANTANES-V3.8'],true)) {
 $ok($first['cellule']===$a);$ok($second['cellule']===['participants'=>null,'long_ouverts'=>null]);$ok($third['cellule']===$c);
 $ok($cases['petit_complement_interne']['masques']===5);
 $ok($cases['historique_inverse']===$second);
 $ok($cases['seuil_historique_superieur']['masques']===2);
 $ok($cases['valeur_masquee_non_zero']['cellule']===['participants'=>20,'long_ouverts'=>null]);
 $ok($cases['complements_stables']['masques']===0);
 $ok($cases['autre_serie']['masques']===2);
 // Balayage de cellules dont les deux effectifs et leur complément sont >= k.
 for($p=10;$p<=30;$p++)for($l=5;$l<=$p-5;$l++){
   $x=['participants'=>$p,'long_ouverts'=>$l];
   for($dp=5;$dp<=9;$dp++)for($dl=5;$dl<=9;$dl++){
     $y=['participants'=>$p+$dp,'long_ouverts'=>$l+$dl];
     if($y['participants']-$y['long_ouverts']<5)continue;
     $r=guard($y,[snapshot($x)]);
     $expected=abs($dp-$dl)>0 && abs($dp-$dl)<5;
     $ok($r['masques']===($expected?2:0));
     $ok(guard($x,[snapshot($y)])['masques']===($expected?2:0));
   }
 }
 // Historique corrompu : fail closed même si la cellule est déjà masquée.
 $bad=snapshot($a);$bad['checksum']=str_repeat('0',64);
 try {guard($b,[$bad]);$ok(false);}catch(RuntimeException $e){$ok($e->getCode()===500&&$e->getMessage()==='atz_integrite');}
}
echo json_encode(['regle'=>ITP_ATZ_REGLE_INST,'assertions_nouvelles'=>$n,'cas'=>$cases],JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),PHP_EOL;
