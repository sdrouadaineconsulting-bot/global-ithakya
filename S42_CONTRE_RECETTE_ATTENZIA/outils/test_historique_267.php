<?php
declare(strict_types=1);

// Contrat du garde de publication, avec nombres abstraits et aucun dossier individuel.
define('ITP_SCHEMA', 'banc_s40');
require $argv[1];
function fail(int $status, string $code, string $message): never {
    throw new RuntimeException($code, $status);
}
function archive(array $cell, string $serie = 'cumul', int $k = 5): array {
    $payload = json_encode(['donnees' => ['univers' => ['mire' => $cell]]], JSON_THROW_ON_ERROR);
    return ['serie' => $serie, 'payload' => $payload, 'checksum' => hash('sha256', $payload), 'k' => $k];
}
$assertions = 0;
function verified(bool $ensured): void {
    global $assertions;
    if (!$ensured) throw new RuntimeException('Contrat de publication incorrect à l’assertion ' . ($assertions + 1));
    $assertions++;
}
function applyGuard(array $cell, array $history, string $serie = 'cumul', int $k = 5): array {
    $data = ['univers' => ['mire' => $cell], 'oeuvres' => ['autre' => ['participants' => 18]]];
    $n = itpAtzMasquerRecoupements($data, $history, $serie, $k);
    verified($data['oeuvres']['autre']['participants'] === 18);
    return [$data['univers']['mire'], $n];
}
for ($reference = 8; $reference <= 15; $reference++) {
    for ($proposal = 5; $proposal <= 20; $proposal++) {
        [$guarded, $count] = applyGuard(['participants' => $proposal], [archive(['participants' => $reference])]);
        $difference = abs($proposal - $reference);
        $expected = $difference > 0 && $difference < 5 ? null : $proposal;
        verified($guarded['participants'] === $expected && $count === ($expected === null ? 1 : 0));
    }
}
$cast = ['participants' => 13, 'taux_approfondissement' => 0.5, 'idees_choisies' => [7, null, null]];
$masked = ['participants' => null, 'taux_approfondissement' => null, 'idees_choisies' => [null, null, null]];
$history = [archive(['participants' => null]), archive(['participants' => 10])];
verified(applyGuard($cast, $history) === [$masked, 3]);
verified(applyGuard($cast, array_reverse($history)) === [$masked, 3]);
verified(applyGuard($cast, [archive(['participants' => 13], 'semaine')]) === [$masked, 3]);
verified(applyGuard($cast, [archive(['participants' => 7], 'cumul', 8)]) === [$masked, 3]);
$ratios = ['participants' => 13, 'taux_approfondissement' => null, 'idees_choisies' => [null, null, null]];
verified(applyGuard($cast, [archive(['participants' => 13, 'taux_approfondissement' => 0.6,
                                   'idees_choisies' => [6, null, null]])]) === [$ratios, 2]);
$broken = archive(['participants'=>11]);
$broken['checksum'] = str_repeat('0',64);
try {
    applyGuard($cast, [$broken]);
    verified(false);
} catch (RuntimeException $error) {
    verified($error->getCode() === 500 && $error->getMessage() === 'atz_integrite');
}
echo json_encode(['assertions' => $assertions, 'resultat' => 'OK'], JSON_THROW_ON_ERROR), PHP_EOL;
