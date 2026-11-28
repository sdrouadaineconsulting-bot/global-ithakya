<?php
declare(strict_types=1);
/* ITHAKYA V1 final — ATTENZIA : instantanés figés (module AJOUTÉ ; le moteur historique ithakya-attenzia.php reste inchangé et en lecture seule).
 * Même interface avec le pilote : constantes ITP_MEMBER_CONTEXTS, ITP_SCHEMA ; fonctions driver(), dbQuery(), itpCatalogueData(), itpAttenziaK() ; appelé par la route dispatchée dans ithakya-pilote.php. */
if (!defined('ITP_SCHEMA')) { http_response_code(404); exit; }

/* ═══════════════════════════ V1 FINAL — ATTENZIA : instantanés figés, protection contre les différences, journal, rétention ═══════════════════════════
 * Moteur analytique privé en banc synthétique ou exploitation privée selon la configuration administrative.
 * Les lectures et réponses observées éclairent l’attention et l’engagement. Ces indicateurs ne sont ni des mesures neurologiques ni des tests psychométriques.
 * Principes : (1) seuls des instantanés IMMUABLES sont consultables (période alignée sur le calendrier, une seule fois) ; (2) k-anonymat + suppression complémentaire ;
 * (3) aucune lecture « vivante » filtrable ; (4) protection des écarts entre instantanés recoupés ; (5) une seule granularité
 * de période par fenêtre de temps ; (6) journal d'audit, limites de consultation et d'export, conservation paramétrable. Les limites sont décrites dans le cockpit. */
const ITP_ATZ_REGLE_INST = 'ATZ-INSTANTANES-V3.5';
const ITP_ATZ_INDICATEURS = ['participants', 'court_termines', 'long_ouverts', 'long_termines', 'long_apres_court', 'quiz_repondus', 'quiz_corrects', 'notes_k_donnees'];
function itpAtzTables(PDO $db): void {
    $fin = driver($db) === 'mysql' ? ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin' : '';
    $db->exec('CREATE TABLE IF NOT EXISTS itp_atz_snapshots (id VARCHAR(32) PRIMARY KEY, serie VARCHAR(8) NOT NULL, cle VARCHAR(10) NOT NULL, debut BIGINT NOT NULL, fin BIGINT NOT NULL, regle VARCHAR(40) NOT NULL, k INTEGER NOT NULL, created_at BIGINT NOT NULL, created_by VARCHAR(32) NOT NULL, checksum VARCHAR(64) NOT NULL, payload TEXT NOT NULL, UNIQUE (serie, cle))' . $fin);
    $db->exec('CREATE TABLE IF NOT EXISTS itp_atz_audit (id VARCHAR(32) PRIMARY KEY, at BIGINT NOT NULL, user_id VARCHAR(32) NOT NULL, action VARCHAR(24) NOT NULL, params VARCHAR(200) NOT NULL, code INTEGER NOT NULL)' . $fin);
}
/* Période alignée : semaine ISO (AAAA-Snn), mois (AAAA-MM) ou arrêté cumulé (AAAA-MM-JJ, inclus). Retourne [début, fin[ en secondes UTC ou null. */
function itpAtzPeriode(string $serie, string $cle): ?array {
    $utc = new DateTimeZone('UTC');
    if ($serie === 'semaine' && preg_match('/^(\d{4})-S(\d{2})$/D', $cle, $m) && (int)$m[2] >= 1 && (int)$m[2] <= 53) {
        $d = (new DateTimeImmutable('now', $utc))->setISODate((int)$m[1], (int)$m[2], 1)->setTime(0, 0);
        if ((int)$d->format('o') !== (int)$m[1] || (int)$d->format('W') !== (int)$m[2]) return null;
        return [$d->getTimestamp(), $d->modify('+7 days')->getTimestamp()];
    }
    if ($serie === 'mois' && preg_match('/^(\d{4})-(\d{2})$/D', $cle, $m) && (int)$m[2] >= 1 && (int)$m[2] <= 12) {
        $d = new DateTimeImmutable($m[1] . '-' . $m[2] . '-01 00:00:00', $utc); return [$d->getTimestamp(), $d->modify('+1 month')->getTimestamp()];
    }
    if ($serie === 'cumul' && preg_match('/^(\d{4})-(\d{2})-(\d{2})$/D', $cle, $m) && checkdate((int)$m[2], (int)$m[3], (int)$m[1])) {
        $d = new DateTimeImmutable($cle . ' 00:00:00', $utc); return [0, $d->modify('+1 day')->getTimestamp()];
    }
    return null;
}
function itpAtzCatalogue(array $config): array {
    $cat = itpCatalogueData($config); $oeuvres = []; $terr = [];
    foreach ((array)($cat['oeuvres'] ?? []) as $o) if (is_array($o) && is_string($o['id'] ?? null)) $oeuvres[$o['id']] = ['univers' => (string)($o['univers'] ?? ''), 'territoires' => array_values(array_filter((array)($o['territoires'] ?? []), 'is_string'))];
    foreach ((array)($cat['territoires'] ?? []) as $t) if (is_array($t) && is_string($t['id'] ?? null)) $terr[$t['id']] = (string)($t['nom'] ?? $t['id']);
    return [$oeuvres, $terr];
}
/* Calcul brut → publication masquée. Une ligne de progression compte pour une personne ; un compte n'est compté qu'une fois par cellule (ensembles par identifiant). */

/* Observabilité du parcours (dictionnaire : docs_v2/DICTIONNAIRE_EVENEMENTS.md). Comptes MEMBRES distincts par événement ; événements DATÉS uniquement ; comportements observables de lecture et de participation. */
const ITP_ATZ_PARCOURS = ['inscriptions', 'court_lances', 'court_termines', 'long_lances', 'long_termines', 'abandons_court', 'contributeurs', 'reconnaissances', 'missions_jouees', 'reprises_lecture', 'reservations_lounge'];
function itpAtzParcours(PDO $db, array $config, int $debut, int $fin, array $lecture): array {
    $k = itpAttenziaK($config);
    $dans = fn(int $t): bool => $t >= $debut && $t < $fin;
    $E = array_replace(array_fill_keys(ITP_ATZ_PARCOURS, []), $lecture);
    foreach (dbQuery($db, "SELECT id, created_at FROM itp_users WHERE role = 'member'", []) as $r) if ($dans((int)$r['created_at'])) $E['inscriptions'][$r['id']] = 1;
    foreach (dbQuery($db, "SELECT e.user_id, e.created_at FROM itp_entries e JOIN itp_users u ON u.id = e.user_id WHERE u.role = 'member' AND " . ITP_ATZ_CONTRIBUTION_VISIBLE, []) as $r) if ($dans((int)$r['created_at'])) $E['contributeurs'][$r['user_id']] = 1;
    try { foreach (dbQuery($db, "SELECT r.user_id, r.created_at FROM itp_reactions r JOIN itp_users u ON u.id = r.user_id WHERE u.role = 'member'", []) as $r) if ($dans((int)$r['created_at'])) $E['reconnaissances'][$r['user_id']] = 1; } catch (Throwable) {}
    foreach (dbQuery($db, "SELECT s.user_id, s.state_key, s.updated_at FROM itp_states s JOIN itp_users u ON u.id = s.user_id WHERE u.role = 'member' AND s.state_key IN ('mission', 'lecture')", []) as $r) if ($dans((int)$r['updated_at'])) $E[$r['state_key'] === 'mission' ? 'missions_jouees' : 'reprises_lecture'][$r['user_id']] = 1;
    try { foreach (dbQuery($db, "SELECT c.user_id, c.requested_at FROM itp_gift_claims c JOIN itp_users u ON u.id = c.user_id WHERE u.role = 'member'", []) as $r) if ($dans((int)$r['requested_at'])) $E['reservations_lounge'][$r['user_id']] = 1; } catch (Throwable) {}
    $cell = []; foreach ($E as $nom => $set) { $n = count($set); $cell[$nom] = $n >= $k ? $n : null; }
    return $cell;
}
function itpAtzCalculer(PDO $db, array $config, int $debut, int $fin, bool $cumul): array {
    $k = itpAttenziaK($config); [$oeuvresCat, $territoiresNoms] = itpAtzCatalogue($config);
    $dans = fn($t): bool => is_int($t) && $t >= $debut && $t < $fin;
    $neuf = fn() => array_fill_keys(ITP_ATZ_INDICATEURS, []) + ['idees' => array_fill(0, 6, []), 'notes' => []];
    $G = ['univers' => [], 'oeuvres' => [], 'territoires' => []];
    $ajoute = function (string $dim, string $cle, string $uid, array $st, array $d, string $workId, int $updatedAt) use (&$G, $dans, $cumul, $neuf): void {
        if (!isset($G[$dim][$cle])) $G[$dim][$cle] = $neuf();
        $g = &$G[$dim][$cle]; $fait = false;
        $cf = $st['court_finished'] ?? null; $ls = $st['long_started'] ?? null; $lf = $st['long_finished'] ?? null;
        if ($dans($cf)) { $g['court_termines'][$uid] = 1; $fait = true; }
        if ($dans($ls)) { $g['long_ouverts'][$uid] = 1; $fait = true; }
        if ($dans($ls) && $dans($lf)) $g['long_termines'][$uid] = 1;
        if ($dans($cf) && $dans($ls) && $ls >= $cf) $g['long_apres_court'][$uid] = 1;
        if ($cumul) {
            $quizOk = is_array($d['quiz'] ?? null) && !array_is_list($d['quiz'])
                && $dans($d['quiz']['at'] ?? $updatedAt);
            if ($quizOk) { $g['quiz_repondus'][$uid] = 1; if (!empty($d['quiz']['correct'])) $g['quiz_corrects'][$uid] = 1; $fait = true; }
            // Comme dans le cockpit, chaque indicateur retient sa propre dernière valeur valide.
            $t = [itpProgressFieldAt($d, 'note_k', $updatedAt), $workId];
            if (is_int($d['note_k'] ?? null) && $d['note_k'] >= 1 && $d['note_k'] <= 5 && $dans(intdiv($t[0], 1000))) {
                $g['notes_k_donnees'][$uid] = 1;
                if (!isset($g['t_note'][$uid]) || $t >= $g['t_note'][$uid]) {
                    $g['notes'][$uid] = $d['note_k'];
                    $g['t_note'][$uid] = $t;
                }
                $fait = true;
            }
            $t = [itpProgressFieldAt($d, 'idea', $updatedAt), $workId];
            if (is_int($d['idea'] ?? null) && $d['idea'] >= 0 && $d['idea'] <= 5 && $dans(intdiv($t[0], 1000))) {
                if (!isset($g['t_idee'][$uid]) || $t >= $g['t_idee'][$uid]) {
                    foreach ($g['idees'] as $ix => $_) unset($g['idees'][$ix][$uid]);
                    $g['idees'][$d['idea']][$uid] = 1;
                    $g['t_idee'][$uid] = $t;
                }
                $fait = true;
            }
        }
        if ($fait) $g['participants'][$uid] = 1;
        unset($g);
    };
    $lecture = array_fill_keys(['court_lances', 'court_termines', 'long_lances', 'long_termines', 'abandons_court'], []);
    // Les trois dimensions et les événements de lecture utilisent la même progression consolidée V4/V5.
    foreach (itpAtzLignesProgression($db) as $r) {
        $d = json_decode($r['data'], true, 16); if (!is_array($d)) continue;
        $st = (is_array($d['steps'] ?? null) && !array_is_list($d['steps'])) ? $d['steps'] : [];
        $uid = $r['user_id'];
        $courtDebut = $st['court_started'] ?? null;
        $courtFin = $st['court_finished'] ?? null;
        if ($dans($courtDebut)) {
            $lecture['court_lances'][$uid] = 1;
            // Une fin postérieure à la fenêtre ou sur une autre œuvre ne clôt pas ce Court.
            if ($courtDebut <= $fin - 86400 && (!is_int($courtFin) || $courtFin < $courtDebut || $courtFin >= $fin)) {
                $lecture['abandons_court'][$uid] = 1;
            }
        }
        if ($dans($courtFin)) $lecture['court_termines'][$uid] = 1;
        if ($dans($st['long_started'] ?? null)) {
            $lecture['long_lances'][$uid] = 1;
            if ($dans($st['long_finished'] ?? null)) $lecture['long_termines'][$uid] = 1;
        }
        $oeuvre = $r['work_id'];
        $updatedAt = (int)$r['updated_at'];
        $ajoute('univers', $r['context_id'], $r['user_id'], $st, $d, $oeuvre, $updatedAt);
        if (!isset($oeuvresCat[$oeuvre])) continue;
        $ajoute('oeuvres', $oeuvre, $r['user_id'], $st, $d, $oeuvre, $updatedAt);
        foreach ($oeuvresCat[$oeuvre]['territoires'] as $territoire) {
            if (isset($territoiresNoms[$territoire])) $ajoute('territoires', $territoire, $r['user_id'], $st, $d, $oeuvre, $updatedAt);
        }
    }
    $pub = function (array $g) use ($k, $cumul): array {
        $n = fn(string $i): int => count($g[$i]);
        $masque = fn(int $x): ?int => $x >= $k ? $x : null;
        $sous = fn(int $x, int $tot): ?int => ($x >= $k && $tot - $x >= $k) ? $x : null;
        $taux = fn(int $a, int $b): ?float => ($a >= $k && $b >= $k && $b - $a >= $k) ? round($a / $b, 3) : null;
        $p = $n('participants'); $notes = array_values($g['notes']);
        $r = ['participants' => $masque($p), 'court_termines' => $sous($n('court_termines'), $p), 'long_ouverts' => $sous($n('long_ouverts'), $p), 'long_termines' => $sous($n('long_termines'), $n('long_ouverts')),
              'long_apres_court' => $sous($n('long_apres_court'), $n('court_termines')),
              'taux_approfondissement' => $taux($n('long_apres_court'), $n('court_termines')), 'taux_achevement_long' => $taux($n('long_termines'), $n('long_ouverts'))];
        if ($cumul) {
            $choix = array_map('count', $g['idees']);
            $repondants = array_sum($choix);
            $r += ['quiz_repondus' => $sous($n('quiz_repondus'), $p), 'quiz_corrects' => $sous($n('quiz_corrects'), $n('quiz_repondus')), 'notes_k_donnees' => $sous($n('notes_k_donnees'), $p),
                   'note_k_moyenne' => (count($notes) >= $k && min($notes) !== max($notes)) ? round(array_sum($notes) / count($notes), 2) : null,
                   'taux_quiz_correct' => $taux($n('quiz_corrects'), $n('quiz_repondus')), 'idees_choisies' => array_map(fn(int $n): ?int => $sous($n, $repondants), $choix)];
        }
        return $r;
    };
    $sortie = [];
    foreach ($G as $dim => $cells) { ksort($cells); foreach ($cells as $cle => $g) $sortie[$dim][$cle] = $pub($g); }
    foreach (['univers' => ITP_MEMBER_CONTEXTS, 'territoires' => array_keys($territoiresNoms), 'oeuvres' => array_keys($oeuvresCat)] as $dim => $attendus)
        foreach ($attendus as $cle) if (!isset($sortie[$dim][$cle])) $sortie[$dim][$cle] = $pub($neuf());   /* cellule vide : tout masqué */
    foreach ($sortie as $dim => $c) ksort($sortie[$dim]);
    $sortie['parcours'] = ['tous' => itpAtzParcours($db, $config, $debut, $fin, $lecture)];
    $sortie['territoires_noms'] = $territoiresNoms;
    return $sortie;
}
function itpAtzIndicateursNumeriques(): array { return ['participants', 'court_termines', 'long_ouverts', 'long_termines', 'long_apres_court', 'quiz_repondus', 'quiz_corrects', 'notes_k_donnees']; }
/* Le masque est calculé avant écriture, sur les valeurs originales, contre tout
 * historique retenu recoupant la période. Un ratio ou une distribution ne doit
 * pas servir de substitut à un effectif masqué. */
function itpAtzMasquerRecoupements(array &$donnees, iterable $historique, string $serie, int $k): int {
    $cellules = [];
    $indicateurs = [];
    foreach ($historique as $ancien) {
        if (!hash_equals($ancien['checksum'], hash('sha256', $ancien['payload']))) {
            fail(500, 'atz_integrite', 'L’historique des instantanés doit être vérifié avant toute nouvelle publication.');
        }
        $snapshot = json_decode($ancien['payload'], true, 16, JSON_THROW_ON_ERROR);
        $seuil = max($k, (int)$ancien['k']);
        foreach (['univers', 'oeuvres', 'territoires', 'parcours'] as $dimension) {
            foreach ($donnees[$dimension] ?? [] as $cle => $valeurs) {
                if (isset($cellules[$dimension][$cle])) continue;
                $precedent = $snapshot['donnees'][$dimension][$cle] ?? [];
                foreach ($valeurs as $indicateur => $valeur) {
                    $autre = $precedent[$indicateur] ?? null;
                    if ($valeur === null || $autre === null) continue;
                    if (is_array($valeur) && is_array($autre)) {
                        if (!array_filter($valeur, 'is_int') || !array_filter($autre, 'is_int')) continue;
                    }
                    if ($ancien['serie'] !== $serie
                        || (is_int($valeur) && is_int($autre) && $valeur !== $autre && abs($valeur - $autre) < $seuil)) {
                        $cellules[$dimension][$cle] = true;
                        break;
                    }
                    if ((is_float($valeur) || is_float($autre) || is_array($valeur)) && $valeur != $autre) {
                        $indicateurs[$dimension][$cle][$indicateur] = true;
                    }
                }
            }
        }
    }
    $nombre = 0;
    foreach (['univers', 'oeuvres', 'territoires', 'parcours'] as $dimension) {
        foreach ($donnees[$dimension] ?? [] as $cle => $valeurs) {
            foreach ($valeurs as $indicateur => $valeur) {
                if ($valeur === null || (!isset($cellules[$dimension][$cle]) && !isset($indicateurs[$dimension][$cle][$indicateur]))) continue;
                if (is_array($valeur)) {
                    $nombre += count(array_filter($valeur, fn($v) => $v !== null));
                    $donnees[$dimension][$cle][$indicateur] = array_fill(0, count($valeur), null);
                } else {
                    $donnees[$dimension][$cle][$indicateur] = null;
                    $nombre++;
                }
            }
        }
    }
    return $nombre;
}
function itpAtzFiger(PDO $db, array $config, array $user, string $serie, string $cle): array {
    // Les vérifications de recoupement et d'espacement doivent être décidées en série.
    if (driver($db) !== 'mysql') return itpAtzFigerSousVerrou($db, $config, $user, $serie, $cle);
    $verrou = 'ith-atz-' . substr(hash('sha256', (string)$db->query('SELECT DATABASE()')->fetchColumn()), 0, 40);
    if ((int)dbQuery($db, 'SELECT GET_LOCK(?, 5)', [$verrou])->fetchColumn() !== 1) {
        fail(503, 'atz_occupe', 'Une création d’instantané est en cours. Réessayez.');
    }
    try {
        $db->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
        $db->beginTransaction();
        $resultat = itpAtzFigerSousVerrou($db, $config, $user, $serie, $cle);
        $db->commit();
        return $resultat;
    } finally {
        if ($db->inTransaction()) $db->rollBack();
        dbQuery($db, 'SELECT RELEASE_LOCK(?)', [$verrou]);
    }
}
function itpAtzFigerSousVerrou(PDO $db, array $config, array $user, string $serie, string $cle): array {
    if (!in_array($serie, ['semaine', 'mois', 'cumul'], true)) fail(422, 'atz_serie', 'Série inconnue (semaine, mois ou cumul).');
    $p = itpAtzPeriode($serie, $cle); if (!$p) fail(422, 'atz_cle', 'Période invalide ou non alignée sur le calendrier.');
    [$debut, $fin] = $p; $now = time();
    if ($fin > $now) fail(409, 'atz_periode_ouverte', 'Seule une période terminée peut être figée.');
    if (dbQuery($db, 'SELECT COUNT(*) FROM itp_atz_snapshots WHERE serie = ? AND cle = ?', [$serie, $cle])->fetchColumn() > 0) fail(409, 'atz_deja_fige', 'Cet instantané existe déjà : il est immuable.');
    if ($serie !== 'cumul') {   /* une seule granularité par fenêtre : pas de recoupement semaine/mois (aucune soustraction possible entre séries) */
        $autre = $serie === 'semaine' ? 'mois' : 'semaine';
        if (dbQuery($db, 'SELECT COUNT(*) FROM itp_atz_snapshots WHERE serie = ? AND debut < ? AND fin > ?', [$autre, $fin, $debut])->fetchColumn() > 0) fail(409, 'atz_recoupement', 'Une période de granularité différente recoupe cette fenêtre.');
    } else {
        $esp = is_int($config['atz_espacement_jours'] ?? null) ? max(1, $config['atz_espacement_jours']) : 7;
        $proche = dbQuery($db, 'SELECT COUNT(*) FROM itp_atz_snapshots WHERE serie = ? AND ABS(fin - ?) < ?', ['cumul', $fin, $esp * 86400])->fetchColumn();
        if ($proche > 0) fail(409, 'atz_espacement', 'Deux instantanés cumulés doivent être espacés d’au moins ' . $esp . ' jours.');
    }
    $k = itpAttenziaK($config); $calc = itpAtzCalculer($db, $config, $debut, $fin, $serie === 'cumul');
    /* C3 — exploitation : UN SEUL niveau de ventilation publié par instantané. Les niveaux sont emboîtés (œuvre ⊂ territoire, univers ≡ œuvre
     * historique, tout ⊂ parcours) : publier deux niveaux permet de retrouver par soustraction un effectif masqué (démontré : territoire 12 − œuvre 9 = 3 < k).
     * Même principe que « une seule granularité de période par fenêtre ». Les autres niveaux, dont le parcours global, sont masqués. Banc : inchangé. */
    if (($GLOBALS['itp_atz_mode'] ?? 'banc') === 'exploitation') {
        $garde = (string)($config['attenzia_exploitation']['dimension'] ?? 'univers');
        $autre = dbQuery($db, "SELECT COUNT(*) FROM itp_atz_snapshots WHERE payload LIKE ? AND payload NOT LIKE ?", ['%"type":"exploitation_privee"%', '%"niveau_publie":"' . $garde . '"%'])->fetchColumn();
        if ($autre > 0) fail(409, 'atz_niveau_change', 'Le niveau de ventilation ne peut pas changer en cours d’exploitation (recoupement entre niveaux).');
        foreach (['univers', 'oeuvres', 'territoires', 'parcours'] as $dim) if ($dim !== $garde) foreach ($calc[$dim] ?? [] as $c => $vals)
            $calc[$dim][$c] = array_map(fn($v) => is_array($v) ? array_map(fn($x) => null, $v) : null, $vals);
        $GLOBALS['itp_atz_dimension'] = $garde;
    }
    $historique = dbQuery($db, 'SELECT serie, payload, checksum, k FROM itp_atz_snapshots WHERE debut < ? AND fin > ?', [$fin, $debut]);
    $masquesInc = itpAtzMasquerRecoupements($calc, $historique, $serie, $k);
    $payload = ['schema' => 'ITHAKYA-ATTENZIA-INSTANTANE-1', 'regle' => ITP_ATZ_REGLE_INST, 'serie' => $serie, 'cle' => $cle, 'debut' => $debut, 'fin' => $fin, 'k' => $k, 'masques_incrementaux' => $masquesInc, 'donnees' => $calc,
        'provenance' => (($GLOBALS['itp_atz_mode'] ?? 'banc') === 'exploitation' ? ['type' => 'exploitation_privee', 'niveau_publie' => $GLOBALS['itp_atz_dimension'] ?? 'univers'] : ['type' => 'banc_synthetique_local']) + ['comptes' => 'rôle membre uniquement', 'collecte_nouvelle' => false],   /* C3 : provenance fidèle au régime */
        'limites' => ['Les étapes de lecture et les participations sont des observations. La continuité Court → Long, les réponses aux quiz, la Note K et les contributions éclairent l’attention, l’engagement et l’appropriation, sans constituer une mesure neurologique ou psychométrique.', 'Les indicateurs de quiz, Note K et idée choisie sont restitués dans la série « cumul ».', 'Un compte est compté une fois par cellule ; les œuvres et territoires se recoupent (un compte peut figurer dans plusieurs cellules).', 'Masque k + suppression complémentaire + contrôle des fenêtres recoupées : aucune garantie d’anonymisation formelle (pas de confidentialité différentielle).', 'Le régime de données figure dans la provenance. En exploitation privée, la restitution applique la ventilation configurée et les seuils de confidentialité.']];
    $json = json_encode($payload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE); $id = bin2hex(random_bytes(16));
    dbQuery($db, 'INSERT INTO itp_atz_snapshots (id, serie, cle, debut, fin, regle, k, created_at, created_by, checksum, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [$id, $serie, $cle, $debut, $fin, ITP_ATZ_REGLE_INST, $k, $now, $user['id'], hash('sha256', $json), $json]);
    return ['id' => $id, 'serie' => $serie, 'cle' => $cle, 'masques_incrementaux' => $masquesInc];
}
function itpAtzLire(PDO $db, string $id): array {
    if (!preg_match('/^[a-f0-9]{32}$/D', $id)) fail(422, 'atz_id', 'Identifiant invalide.');
    $r = dbQuery($db, 'SELECT * FROM itp_atz_snapshots WHERE id = ?', [$id])->fetch(PDO::FETCH_ASSOC); if (!$r) fail(404, 'atz_absent', 'Instantané inconnu.');
    if (!hash_equals($r['checksum'], hash('sha256', $r['payload']))) fail(500, 'atz_integrite', 'Instantané altéré : empreinte invalide.');
    return ['meta' => ['id' => $r['id'], 'serie' => $r['serie'], 'cle' => $r['cle'], 'created_at' => (int)$r['created_at'], 'checksum' => $r['checksum']], 'instantane' => json_decode($r['payload'], true)];
}
/* L’administrateur configure l’exploitation privée. Habilitation nominative, échéance, ventilation unique, seuil k et conservation sont contrôlés à chaque appel. Le banc synthétique reste distinct. */
function itpAtzExploitation(array $config, bool $local, ?array $user): ?string {
    $e = $config['attenzia_exploitation'] ?? null;
    if ($local || !is_array($e)) return 'attenzia_lab_only';
    $adm = $e['administrateurs'] ?? null;
    if (!is_array($adm) || !$adm || count(array_filter($adm, fn($x) => is_string($x) && preg_match('/^[a-f0-9]{32}$/D', $x))) !== count($adm)) return 'administrateurs';
    $fin = is_string($e['jusqu_au'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/D', $e['jusqu_au']) ? strtotime($e['jusqu_au'] . ' 23:59:59 UTC') : false;
    if ($fin === false || $fin < time()) return 'echeance';
    if (!in_array($e['dimension'] ?? 'univers', ['univers', 'oeuvres', 'territoires'], true)) return 'dimension';
    if (!is_int($config['attenzia_k'] ?? null) || $config['attenzia_k'] < 5) return 'k';
    if (!is_int($config['atz_conservation_jours'] ?? null) || $config['atz_conservation_jours'] < 30) return 'conservation';
    if (!$user || ($user['role'] ?? '') !== 'admin' || !in_array($user['id'], $adm, true)) return 'administrateur_non_autorise';
    return null;
}
function itpAtzHandle(PDO $db, array $config, ?array $user, string $action, string $method, array $input, bool $local): void {
    if (!in_array($action, ['attenzia_instantane_creer', 'attenzia_instantanes', 'attenzia_instantane', 'attenzia_comparer', 'attenzia_export', 'attenzia_journal', 'attenzia_purger'], true)) return;
    if (($config['attenzia_agregats'] ?? false) !== true) fail(403, 'attenzia_disabled', 'ATTENZIA est désactivé dans la configuration d’administration.');
    /* Journal d'audit : UNE ligne par appel (succès comme refus, y compris 403/405/409/422/429), écrite à l'arrêt avec le code HTTP final. Aucun contenu de donnée, uniquement action + paramètres de la demande. */
    $qui = $user['id'] ?? 'anonyme'; $acte = substr($action, 9);
    $demande = array_intersect_key($_GET, array_flip(['id', 'a', 'b'])) + array_intersect_key($input, array_flip(['serie', 'cle', 'confirmer']));
    register_shutdown_function(function () use ($db, $qui, $acte, $demande) {
        try { if ($db->inTransaction()) $db->rollBack(); dbQuery($db, 'INSERT INTO itp_atz_audit (id, at, user_id, action, params, code) VALUES (?, ?, ?, ?, ?, ?)', [bin2hex(random_bytes(16)), time(), $qui, substr($acte, 0, 24), substr(json_encode($demande + ($GLOBALS['itp_atz_extra'] ?? []), JSON_UNESCAPED_UNICODE), 0, 200), (int)http_response_code()]); } catch (Throwable) {}
    });
    itpAtzTables($db);
    if (!$user || $user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administration d’ITHAKYA.');
    /* C3 — deux régimes exclusifs. BANC : local + attenzia_banc_synthetique (inchangé). EXPLOITATION PRIVÉE (bêta) : hors local seulement,
     * bloc attenzia_exploitation complet et administrateur nommément autorisé (voir itpAtzExploitation). La lecture « vivante »
     * (route attenzia_agregats du pilote) reste réservée au banc : seuls les instantanés figés, conçus contre les déductions par différence, sont ouverts. */
    $banc = $local && ($config['attenzia_banc_synthetique'] ?? false) === true;
    if (!$banc) {
        $refus = itpAtzExploitation($config, $local, $user);
        if ($refus === 'attenzia_lab_only') fail(403, 'attenzia_lab_only', 'Lecture réservée au banc synthétique local.');
        if ($refus !== null) { $GLOBALS['itp_atz_extra'] = ['refus' => $refus]; fail(403, 'attenzia_exploitation', 'Exploitation ATTENZIA non autorisée pour ce compte ou cette configuration.'); }
    }
    $GLOBALS['itp_atz_mode'] = $banc ? 'banc' : 'exploitation';
    $get = fn(string $k): ?string => isset($_GET[$k]) && is_string($_GET[$k]) ? $_GET[$k] : null;
    $permis = ['attenzia_instantane_creer' => [], 'attenzia_instantanes' => [], 'attenzia_instantane' => ['id'], 'attenzia_comparer' => ['a', 'b'], 'attenzia_export' => ['id'], 'attenzia_journal' => [], 'attenzia_purger' => []][$action];
    if (array_diff(array_keys($_GET), array_merge(['action'], $permis))) { fail(422, 'attenzia_filter', 'Aucun filtre libre : paramètres non reconnus.'); }
    $ecrit = in_array($action, ['attenzia_instantane_creer', 'attenzia_purger'], true);
    if ($ecrit !== ($method === 'POST')) fail(405, 'method', 'Méthode non autorisée pour cette action.');
    $lim = ['attenzia_instantane_creer' => [10, 3600], 'attenzia_purger' => [5, 3600], 'attenzia_export' => [5, 86400]][$action] ?? [60, 3600];
    throttle($db, 'atz_' . $action, $user['id'], $lim[0], $lim[1], $config);
    $a = substr($action, 9);
    if ($action === 'attenzia_instantane_creer') {
        fields($input, ['serie', 'cle']); $r = itpAtzFiger($db, $config, $user, (string)($input['serie'] ?? ''), (string)($input['cle'] ?? ''));
        output(['ok' => true] + $r, 201);
    }
    if ($action === 'attenzia_instantanes') {
        $rows = dbQuery($db, 'SELECT id, serie, cle, debut, fin, k, created_at, checksum FROM itp_atz_snapshots ORDER BY serie, debut', [])->fetchAll(PDO::FETCH_ASSOC);
        output(['ok' => true, 'mode' => $GLOBALS['itp_atz_mode'], 'instantanes' => $rows]);
    }
    if ($action === 'attenzia_instantane') { $r = itpAtzLire($db, (string)$get('id')); output(['ok' => true] + $r); }
    if ($action === 'attenzia_comparer') {
        $A = itpAtzLire($db, (string)$get('a')); $B = itpAtzLire($db, (string)$get('b'));
        if ($A['meta']['serie'] !== $B['meta']['serie']) fail(422, 'atz_series', 'Comparaison possible entre instantanés de la même série.');
        $delta = []; $da = $A['instantane']['donnees']; $db_ = $B['instantane']['donnees'];
        foreach (['univers', 'oeuvres', 'territoires', 'parcours'] as $dim) foreach ($db_[$dim] ?? [] as $c => $vals) foreach (array_keys(array_filter($vals, fn($v) => is_int($v) || $v === null)) as $i) {
            $x = $da[$dim][$c][$i] ?? null; $y = $vals[$i] ?? null;
            $delta[$dim][$c][$i] = ($x !== null && $y !== null) ? ['a' => $x, 'b' => $y, 'delta' => $y - $x] : null;   /* jamais de différence dérivée d’une valeur masquée */
        }
        output(['ok' => true, 'a' => $A['meta'], 'b' => $B['meta'], 'delta' => $delta, 'note' => 'Une différence n’est calculée que si les deux valeurs sont publiées (≥ k).']);
    }
    if ($action === 'attenzia_export') {
        $r = itpAtzLire($db, (string)$get('id')); $lignes = ["dimension;cle;indicateur;valeur"];
        foreach (['univers', 'oeuvres', 'territoires', 'parcours'] as $dim) foreach ($r['instantane']['donnees'][$dim] ?? [] as $c => $vals) foreach ($vals as $i => $v) if (!is_array($v)) $lignes[] = $dim . ';' . $c . ';' . $i . ';' . ($v === null ? '' : $v);
        header('Content-Type: text/csv; charset=utf-8'); header('Content-Disposition: attachment; filename="attenzia-' . $r['meta']['serie'] . '-' . $r['meta']['cle'] . '.csv"'); header('X-Content-Type-Options: nosniff');
        echo implode("\n", $lignes) . "\n"; exit;
    }
    if ($action === 'attenzia_journal') {
        $rows = dbQuery($db, 'SELECT at, user_id, action, params, code FROM itp_atz_audit ORDER BY at DESC, id DESC LIMIT 100', [])->fetchAll(PDO::FETCH_ASSOC);
        output(['ok' => true, 'journal' => $rows]);
    }
    if ($action === 'attenzia_purger') {   /* conservation paramétrable (atz_conservation_jours, ≥ 30, défaut 400) ; l'audit de la purge est conservé */
        fields($input, ['confirmer']); if (($input['confirmer'] ?? null) !== true) fail(422, 'atz_confirmation', 'Confirmation explicite requise.');
        $jours = is_int($config['atz_conservation_jours'] ?? null) ? max(30, $config['atz_conservation_jours']) : 400; $seuil = time() - $jours * 86400;
        $n1 = dbQuery($db, 'DELETE FROM itp_atz_snapshots WHERE created_at < ?', [$seuil])->rowCount(); $n2 = dbQuery($db, 'DELETE FROM itp_atz_audit WHERE at < ?', [$seuil])->rowCount();
        $GLOBALS['itp_atz_extra'] = ['supprimes' => $n1, 'audit' => $n2, 'jours' => $jours];
        output(['ok' => true, 'instantanes_supprimes' => $n1, 'lignes_audit_supprimees' => $n2, 'conservation_jours' => $jours]);
    }
}
