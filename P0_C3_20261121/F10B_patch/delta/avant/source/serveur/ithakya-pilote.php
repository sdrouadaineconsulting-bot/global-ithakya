<?php
declare(strict_types=1);
ini_set('display_errors', '0'); ini_set('log_errors', '1');   /* CE1 : aucun message d'erreur PHP dans les réponses (journal seulement) */

/* ITHAKYA — compte commun du pilote privé, quatre univers membres + espace partenaire, schéma de données v4.
 * v4 (21/10/2026, refonte) : signalements et modération (itp_reports), progression calculée sur le serveur
 * (barème validé des univers, sans double gain), Communauté globale (fil des quatre univers), découvertes gardées
 * du catalogue et positions de lecture (états « gardes » et « lecture »). Ajout d'une table seulement.
 * v3 (20/10/2026) : récupération de l'accès (code personnel, lien de réinitialisation émis par l'administrateur),
 * état serveur de la Grande Traversée, déconnexion des autres appareils. Ajouts uniquement : aucune table v2 n'est modifiée.
 * Aucun secret dans la racine web. Les outils privés (migration, sauvegarde, récupération)
 * incluent ce fichier en mode bibliothèque : aucune requête n'est alors traitée. */

/* v5 (25/10/2026, M2 — plusieurs œuvres par univers, PROTOTYPE PRIVÉ) : l'œuvre devient l'unité de progression.
 * Ajouts uniquement : table itp_work_progress (une ligne par compte et par œuvre) et colonne itp_entries.work_id (NULL
 * pour les contributions antérieures = œuvre historique de l'univers). itp_progress2 est conservée et continue d'être
 * écrite pour l'œuvre historique de chaque univers (écriture double) : un retour à l'API v4 retrouve exactement les
 * parcours historiques. Le barème, les Grades, les plafonds et la règle des cinq idées sont inchangés (M1 non arbitré). */
/* v6 — accusés de lecture individualisés par discussion et œuvre ; migration privée additive obligatoire pour une base v5. */
const ITP_SCHEMA = 6;
require_once __DIR__ . '/ithakya-pilot-policy.php';
require_once __DIR__ . '/ithakya-waitlist.php';
require_once __DIR__ . '/ithakya-economy.php';
require_once __DIR__ . '/ithakya-cadeaux.php';
require_once __DIR__ . '/ithakya-attenzia.php';
require_once __DIR__ . '/ithakya-attenzia-instantanes.php';
require_once __DIR__ . '/ithakya-lecture-preuve.php';
require_once __DIR__ . '/ithakya-credit-review.php';
/* V1 : missions narratives (ink). Aucun Point, aucun XP : l'état ne fait que mémoriser le parcours du membre. */
const ITP_MISSIONS = ['poussiere' => ['relations', 'origines', 'consequences']];
const ITP_TRAVERSEE = ['science' => ['relations', 'origines', 'consequences'], 'culture' => ['gestes', 'equipe', 'preparation'], 'sport' => ['observation', 'adaptation', 'collectif']];
const ITP_RESET_TTL = 86400;
/* Contextes autorisés : identifiant stable => nombre d'idées du Long.
 * 20/10/2026 : « retail » est l'espace Retail Media partenaire ; il n'est ouvert qu'aux rôles de ITP_PARTNER_ROLES (contrôle serveur). */
const ITP_CONTEXTS = ['signature' => 5, 'pop' => 5, 'progression' => 5, 'soleil' => 5, 'culture' => 5, 'societe' => 5, 'retail' => 5];
/* S1 (25/10/2026) — Cinq territoires publics => contexte technique de gain et de discussion. Les contextes « signature »,
 * « pop », « progression » et « soleil » sont des identifiants historiques conservés tels quels ; « culture » et « societe »
 * n'ont pas d'œuvre historique (aucune contribution sans œuvre déclarée). Une œuvre a UN contexte (celui de son territoire
 * principal) : l'inscrire dans d'autres territoires ne crée ni second parcours ni second gain. */
const ITP_TERRITOIRES = ['sciences-tech' => 'signature', 'culture-creation' => 'culture', 'sport-aventure' => 'progression',
                         'societe-impact' => 'societe', 'pop-culture' => 'pop'];
const ITP_LEGACY_TERRITOIRES = ['signature' => 'sciences-tech', 'soleil' => 'sciences-tech', 'progression' => 'sport-aventure', 'pop' => 'pop-culture'];
/* R13 : plancher temporel d'un visionnage observé, sans modifier le barème. La
 * couverture transmise par le navigateur n'est pas une preuve infalsifiable : la
 * validation réelle et la prévention de fraude restent des réserves bêta. */
const ITP_MEDIA_TIMING = ['court' => ['signature' => 15, 'pop' => 15, 'progression' => 15, 'soleil' => 12, 'culture' => 15, 'societe' => 15],
                          'long'  => ['signature' => 40, 'pop' => 40, 'progression' => 40, 'soleil' => 40, 'culture' => 40, 'societe' => 40]];
const ITP_PARTNER_ROLES = ['partner', 'admin'];
const ITP_PARTNER_CONTEXTS = ['retail'];
const ITP_STEPS = ['court_started', 'court_finished', 'long_started', 'long_finished', 'quiz_answered'];
const ITP_MEMBER_CONTEXTS = ['signature', 'pop', 'progression', 'soleil', 'culture', 'societe'];
/* Barème validé repris tel quel des univers (ITHAKYA_BAREME, pages du 15/10/2026) et huit Grades (CONFIG.grades).
 * Version de règle inscrite dans chaque ligne du journal. La Note K, les favoris et la consultation d'un programme ne rapportent rien. */
const ITP_RULES = 'bareme-2026-10-15';
const ITP_BAREME = [
    'xp' => ['court' => 5, 'long' => 25, 'quiz' => 5, 'quizOk' => 10, 'quest' => 10, 'universe' => 50],
    'pts' => ['court' => 0, 'long' => 10, 'quiz' => 2, 'quizOk' => 4, 'quest' => 5],
    'ms' => ['long' => [[1, 20], [3, 30], [10, 100], [25, 250]], 'quiz' => [[1, 10], [5, 25], [15, 75], [40, 200]], 'quest' => [[1, 20], [3, 75], [10, 250]]],
    'ev' => ['long' => [25, 250], 'quiz' => [40, 200], 'quest' => [10, 250]],
    'gradeBonus' => [0, 50, 100, 150, 200, 250, 300, 500],
];
const ITP_GRADES = [['Curieuse', 0], ['Exploratrice', 600], ['Éclaireuse', 1800], ['Contributrice', 4200], ['Cartographe', 8000], ['Passeuse', 13500], ['Référente', 21000], ['Pionnière', 32000]];
/* Bonne réponse du quiz de chaque Long (catalogue, champ quiz.bonne). */
/* M10 (02/11/2026) : index de la bonne réponse aligné sur catalogue.json (ordre varié ; les réponses déjà enregistrées gardent leur statut stocké). */
const ITP_QUIZ = ['signature' => 1, 'pop' => 2, 'progression' => 0, 'soleil' => 1, 'retail' => 0];
/* M2 — Œuvre historique de chaque univers : identifiant stable, jamais réattribué. Les pages d'univers existantes
 * continuent d'envoyer « context » seul ; le serveur les rattache à cette œuvre. */
const ITP_LEGACY_WORKS = ['signature' => 'ith-signature-lien', 'pop' => 'ith-pop-moment', 'progression' => 'ith-progression-elan',
                          'soleil' => 'ith-soleil-courant', 'retail' => 'ith-retail-choix'];
const ITP_WORK_ID = '/^[a-z0-9][a-z0-9-]{2,47}$/D';
const ITP_WORK_STATUSES = ['disponible', 'essai_prive', 'retiree'];
/* M1 non arbitré : un Long compte exactement cinq idées. Passer à true n'est permis qu'après décision explicite. */
const ITP_M1_IDEES_VARIABLES = false;
const ITP_REPORT_REASONS = ['hors_sujet' => 'Hors sujet', 'irrespectueux' => 'Propos irrespectueux', 'donnees_personnelles' => 'Données personnelles exposées', 'autre' => 'Autre motif'];

final class PilotError extends RuntimeException {
    public function __construct(public int $status, public string $kind, string $message) {
        parent::__construct($message);
    }
}

function fail(int $status, string $kind, string $message): never {
    throw new PilotError($status, $kind, $message);
}
function output(array $value, int $status = 200): never {
    http_response_code($status);
    echo json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}
function text(mixed $value, int $minimum, int $maximum): string {
    if (!is_string($value) || strlen($value) > $maximum * 4 || !preg_match('//u', $value)) {
        fail(422, 'invalid_text', 'Le texte contient des caractères non valides.');
    }
    $value = trim(str_replace(["\r\n", "\r"], "\n", $value));
    $length = preg_match_all('/./us', $value);
    if ($length < $minimum || $length > $maximum || preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', $value)) {
        fail(422, 'invalid_text', "Le texte doit contenir entre $minimum et $maximum caractères.");
    }
    return $value;
}
function inputMediaType(string $header): string {
    return strtolower(trim(explode(';', $header, 2)[0]));
}
function fields(array $input, array $allowed): void {
    if (array_diff(array_keys($input), $allowed)) {
        fail(422, 'unknown_field', 'Un champ de cette demande n’est pas reconnu.');
    }
}
function dbQuery(PDO $db, string $sql, array $params = []): PDOStatement {
    $stmt = $db->prepare($sql);
    $stmt->execute($params);
    return $stmt;
}
function driver(PDO $db): string {
    return (string)$db->getAttribute(PDO::ATTR_DRIVER_NAME);
}
function passwordMaterial(string $password, array $config): string {
    return base64_encode(hash_hmac('sha384', $password, $config['password_pepper'], true));
}
function checkedPassword(mixed $password): string {
    if (!is_string($password) || strlen($password) > 1024 || !preg_match('//u', $password)
        || preg_match_all('/./us', $password) < 15 || preg_match_all('/./us', $password) > 256
        || trim($password) === '') {
        fail(422, 'password_length', 'Choisissez une phrase de passe de 15 à 256 caractères.');
    }
    return $password;
}
function hashPassword(string $password, array $config): string {
    $material = passwordMaterial($password, $config);
    if (defined('PASSWORD_ARGON2ID')) {
        return password_hash($material, PASSWORD_ARGON2ID, ['memory_cost' => 19456, 'time_cost' => 2, 'threads' => 1]);
    }
    return password_hash($material, PASSWORD_BCRYPT, ['cost' => 12]);
}
function cleanProfile(array $input, ?PDO $db = null, ?string $actuel = null): array {
    $name = text($input['display_name'] ?? '', 2, 40);
    /* M09 : sans avatar fourni, une mise à jour de profil CONSERVE l'avatar actuel (auparavant : retour silencieux à « ocean »). */
    $avatar = $input['avatar'] ?? ($actuel ?? 'ocean');
    /* M09 : identifiant contrôlé par le registre en base (présent et ouvert) ; l'avatar actuel d'un profil reste accepté. */
    if (!is_string($avatar) || !($avatar === $actuel || ($db ? itpAvatarAutorise($db, $avatar) : (in_array($avatar, ITP_AVATARS_CLASSIQUES, true) || preg_match(ITP_AVATAR_MOTIF, $avatar) === 1)))) {
        fail(422, 'avatar', 'Choisissez un des avatars proposés.');
    }
    $interests = $input['interests'] ?? [];
    $choices = ['sciences', 'nature', 'creation', 'sport', 'societe', 'commerce', 'pop'];
    if (!is_array($interests) || !array_is_list($interests) || count($interests) > 7) {
        fail(422, 'interests', 'Les centres d’intérêt ne sont pas valides.');
    }
    foreach ($interests as $interest) {
        if (!is_string($interest) || !in_array($interest, $choices, true)) {
            fail(422, 'interests', 'Choisissez les centres d’intérêt proposés.');
        }
    }
    return [$name, $avatar, json_encode(array_values(array_unique($interests)), JSON_THROW_ON_ERROR)];
}
/* M09 — Registre des avatars en base : tables dédiées itp_avatar* (migration privée migration_avatars_m09_mysql.sql + seed
 * idempotent). Le compte n'enregistre qu'un identifiant présent et OUVERT. Sans migration : repli sur la liste figée M08.
 * Les portraits ne sont servis (action avatar_image) que s'ils sont « enabled » (revue ≥ 85/100 + contrôle technique + droits
 * + activation par un second compte) ; les URL portent l'empreinte (?v=) pour invalider les caches lors d'un remplacement. */
const ITP_AVATARS_CLASSIQUES = ['ocean', 'terre', 'aurore', 'corail', 'foret', 'nuit'];
const ITP_AVATAR_MOTIF = '/^(?:av0[1-6](?:0[1-9]|10)|av10(?:0[1-9]|[1-8][0-9]|90))$/D';
const ITP_AVATAR_TAILLES = [64, 128, 256, 512];
/* P1 : catalogue vectoriel additionnel. Les identifiants et le registre M09 restent autonomes. */
function itpAvatarVariantesP1(): array {
    static $variantes = null;
    if ($variantes !== null) return $variantes;
    $variantes = [];
    $dossier = dirname(__DIR__) . '/assets/avatars/p1/';
    if (!is_file($dossier . 'collection.json')) return $variantes;
    $collection = json_decode(file_get_contents($dossier . 'collection.json'), true, 8, JSON_THROW_ON_ERROR);
    foreach ($collection as $id => $item) {
        if (!preg_match('/^avp[0-9]{3}$/D', $id) || !is_file($dossier . $id . '.svg')) continue;
        $variantes[$id] = ['id' => $id, 'nom' => $item['nom'], 'famille' => $item['famille'], 'classique' => false,
            'ouvert' => true, 'portrait_valide' => false, 'variante_de' => $item['parent'],
            'image' => 'assets/avatars/p1/' . $id . '.svg?v=' . substr(hash_file('sha256', $dossier . $id . '.svg'), 0, 12),
            'tailles' => (object)[]];
    }
    return $variantes;
}
/* P2 : portraits illustrés de la candidate. Le choix reste un ID de profil ;
 * les masters et la procédure de publication M09 sont séparés. */
function itpAvatarPortraitsP2(): array {
    static $portraits = null;
    if ($portraits !== null) return $portraits;
    $portraits = [];
    $dossier = dirname(__DIR__) . '/assets/avatars/p2/';
    if (!is_file($dossier . 'collection.json')) return $portraits;
    $collection = json_decode(file_get_contents($dossier . 'collection.json'), true, 8, JSON_THROW_ON_ERROR);
    foreach ($collection as $id => $item) {
        if (!preg_match('/^avq2[0-9]{2}$/D', $id)) continue;
        $tailles = [];
        foreach (ITP_AVATAR_TAILLES as $taille) {
            $nom = $id . '-' . $taille . '.webp';
            if (is_file($dossier . $nom)) $tailles[$taille] = 'assets/avatars/p2/' . $nom . '?v=' . substr(hash_file('sha256', $dossier . $nom), 0, 12);
        }
        if (!isset($tailles[64], $tailles[128])) continue;
        $portraits[$id] = ['id' => $id, 'nom' => $item['nom'], 'famille' => $item['famille'], 'classique' => false,
            'ouvert' => true, 'portrait_valide' => false, 'variante_de' => $item['parent'],
            'image' => $tailles[64], 'tailles' => (object)$tailles];
    }
    return $portraits;
}
function itpAvatarCatalogue(?PDO $db = null): ?array {
    static $cat = false;
    if ($cat !== false) return $cat;
    if ($db === null) return null;
    try { $rows = dbQuery($db, 'SELECT id, nom, famille, classique, selection, portrait_statut FROM itp_avatars ORDER BY classique DESC, id')->fetchAll(); }
    catch (PDOException) { return $cat = null; }
    $assets = [];
    foreach (dbQuery($db, "SELECT avatar_id, role, path, sha256 FROM itp_avatar_assets WHERE role <> 'source' ORDER BY id")->fetchAll() as $a) $assets[$a['avatar_id']][$a['role']] = $a;
    $cat = [];
    foreach ($rows as $r) {
        $id = $r['id']; $img = null; $tailles = [];
        if ($r['portrait_statut'] === 'enabled') {
            foreach (ITP_AVATAR_TAILLES as $t) if (isset($assets[$id]['portrait_' . $t]))
                $tailles[$t] = 'api/ithakya-pilote.php?action=avatar_image&id=' . $id . '&t=' . $t . '&v=' . substr($assets[$id]['portrait_' . $t]['sha256'], 0, 12);
            $img = $tailles[128] ?? null;
        }
        if ($img === null && isset($assets[$id]['provisoire']) && preg_match('~^assets/avatars/[a-z0-9]{2,8}\.svg$~D', $assets[$id]['provisoire']['path']))
            $img = $assets[$id]['provisoire']['path'] . '?v=' . substr($assets[$id]['provisoire']['sha256'], 0, 12);
        $cat[$id] = ['id' => $id, 'nom' => $r['nom'], 'famille' => $r['famille'], 'classique' => (bool)$r['classique'], 'ouvert' => $r['selection'] === 'ouverte',
            'portrait_valide' => $r['portrait_statut'] === 'enabled' && $tailles !== [], 'image' => $img, 'tailles' => (object)$tailles];
    }
    return $cat;
}
function itpAvatarAutorise(PDO $db, mixed $avatar): bool {
    if (!is_string($avatar) || strlen($avatar) > 16) return false;
    if (isset(itpAvatarVariantesP1()[$avatar]) || isset(itpAvatarPortraitsP2()[$avatar])) return true;
    $cat = itpAvatarCatalogue($db);
    if ($cat === null) return in_array($avatar, ITP_AVATARS_CLASSIQUES, true) || preg_match(ITP_AVATAR_MOTIF, $avatar) === 1;
    return isset($cat[$avatar]) && $cat[$avatar]['ouvert'];
}
function itpAvatarImage(mixed $avatar): ?string {
    if (!is_string($avatar)) return null;
    return itpAvatarPortraitsP2()[$avatar]['image'] ?? itpAvatarVariantesP1()[$avatar]['image'] ?? itpAvatarCatalogue()[$avatar]['image'] ?? null;
}
function itpAvatarRolesP2(PDO $db, array $user): array {
    if ($user['role'] === 'admin') return ['admin'];
    try { return dbQuery($db, 'SELECT role FROM itp_admin_roles WHERE user_id = ?', [$user['id']])->fetchAll(PDO::FETCH_COLUMN); } catch (PDOException) { return []; }
}
function itpAvatarVersion(PDO $db, string $id, ?string $par, string $motif): void {
    $a = dbQuery($db, 'SELECT * FROM itp_avatars WHERE id = ?', [$id])->fetch();
    dbQuery($db, 'INSERT INTO itp_avatar_versions (avatar_id, version, changed_at, changed_by, motif, snapshot) VALUES (?, ?, ?, ?, ?, ?)',
        [$id, (int)$a['version'], time(), $par, $motif, json_encode($a, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR)]);
}
/* Contrôle technique d'un portrait : source + 4 dérivés carrés présents dans le stockage privé, octets et SHA-256 conformes. */
function itpAvatarControleTechnique(PDO $db, array $config, string $id): array {
    $pb = []; $roles = [];
    foreach (dbQuery($db, 'SELECT * FROM itp_avatar_assets WHERE avatar_id = ? ORDER BY id', [$id])->fetchAll() as $a) $roles[$a['role']] = $a;
    foreach (array_merge(['source'], array_map(fn($t) => 'portrait_' . $t, ITP_AVATAR_TAILLES)) as $role) {
        $a = $roles[$role] ?? null;
        if (!$a) { $pb[] = $role . ' : absent du registre'; continue; }
        if ($a['stockage'] !== 'prive' || !preg_match('~^avatars/(sources|derives)/av[0-9]{4}/[a-z0-9_]{1,40}\.(png|webp)$~D', $a['path'])) { $pb[] = $role . ' : chemin hors liste blanche'; continue; }
        $f = $config['_private'] . '/' . $a['path'];
        if (!is_file($f) || is_link($f)) { $pb[] = $role . ' : fichier absent'; continue; }
        if (filesize($f) !== (int)$a['bytes'] || hash_file('sha256', $f) !== $a['sha256']) { $pb[] = $role . ' : empreinte divergente'; continue; }
        if (str_starts_with($role, 'portrait_')) { $t = (int)substr($role, 9); $d = @getimagesize($f); if (!$d || $d[0] !== $t || $d[1] !== $t) $pb[] = $role . ' : dimensions non conformes'; }
    }
    return $pb;
}
function publicUser(array $user): array {
    return ['id' => $user['id'], 'login' => $user['login'], 'display_name' => $user['display_name'],
        'avatar' => $user['avatar'], 'avatar_image' => itpAvatarImage($user['avatar']), 'interests' => json_decode($user['interests'], true, 8, JSON_THROW_ON_ERROR),
        'is_admin' => $user['role'] === 'admin', 'is_partner' => isPartner($user)];
}
function isPartner(?array $user): bool { return $user !== null && in_array($user['role'] ?? '', ITP_PARTNER_ROLES, true); }
/* Univers accessibles à ce compte : les quatre univers utilisateurs, plus l'espace partenaire pour les rôles autorisés. */
function allowedContexts(?array $user): array {
    return array_values(array_filter(array_keys(ITP_CONTEXTS), fn(string $c): bool => !in_array($c, ITP_PARTNER_CONTEXTS, true) || isPartner($user)));
}
function resetSession(): void {
    $now = time();
    /* Une requête en vol avec l'ancien cookie doit trouver une session anonyme,
     * sans émettre un cookie qui écraserait le nouvel identifiant du navigateur. */
    $_SESSION = ['csrf' => bin2hex(random_bytes(32)), 'created_at' => $now,
        'last_seen' => $now, 'rotated_at' => $now];
    if (!session_regenerate_id(false)) fail(503, 'session', 'La connexion au pilote est momentanément indisponible.');
    unset($_SESSION['rotated_at']);
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
function loggedUser(PDO $db): ?array {
    if (empty($_SESSION['user_id'])) return null;
    $user = dbQuery($db, 'SELECT * FROM itp_users WHERE id = ?', [$_SESSION['user_id']])->fetch();
    if (!$user || (int)$user['auth_version'] !== (int)($_SESSION['auth_version'] ?? -1)) {
        resetSession();
        return null;
    }
    return $user;
}
function authenticated(?array $user): array {
    if (!$user) fail(401, 'login_required', 'Connectez-vous au pilote pour continuer.');
    return $user;
}
/* R13-H : l'identité de la lecture est figée au lancement côté navigateur.
 * Une requête retardée durant A -> B ne doit jamais sauvegarder la position
 * de A sur B, même si les cookies de session ont changé entre-temps.
 * Ce contrôle est un garde-fou d'intégrité ; il ne remplace pas la session PHP. */
function assertLectureOwner(mixed $owner, array $user): void {
    if (!is_string($owner) || !preg_match('/^[a-f0-9]{32}$/D', $owner)
        || !hash_equals((string)$user['id'], $owner)) {
        fail(409, 'session_changed', 'La session a changé : cette position de lecture n’a pas été enregistrée.');
    }
}
/* R14 : frontière d'appartenance des brouillons de Communauté à la publication. */
/* L'effacement exclusif interdit des mutations mêlées ou silencieuses. */
function isStateResetOnly(array $input): bool {
    return ($input['reset'] ?? false) === true
        && isset($input['key'], $input['owner_id'])
        && count($input) === 3;
}
function assertContributionOwner(mixed $owner, array $user): void {
    if (!is_string($owner) || !preg_match('/^[a-f0-9]{32}$/D', $owner)
        || !hash_equals((string)$user['id'], $owner)) {
        fail(409, 'session_changed', 'Le compte a changé : cette contribution n’a pas été publiée.');
    }
}
/* R7 — Empêche l'exécution d'une action préparée sous le compte A
 * après une bascule de cookie vers B, même lorsque B est aussi administrateur. */
function assertActionOwner(mixed $owner, array $user): void {
    if (!is_string($owner) || !preg_match('/^[a-f0-9]{32}$/D', $owner)
        || !hash_equals((string)$user['id'], $owner)) {
        fail(409, 'session_changed', 'Le compte a changé : cette action n’a pas été exécutée.');
    }
}
/* R14 — Une clé de publication déjà consommée par une contribution retirée
 * ne doit JAMAIS être acquittée comme une publication active. L'idempotence
 * s'applique à une contribution visible, pas à sa restauration implicite.
 * Appelée également après collision UNIQUE (deux envois concurrents). */
function assertActivePublicationRetry(array $previous, string $bodyHash): void {
    if (!hash_equals((string)$previous['body_hash'], $bodyHash)) {
        fail(409, 'request_reused', 'Cette demande correspond déjà à un autre texte.');
    }
    if (($previous['removed_at'] ?? null) !== null) {
        fail(409, 'entry_removed', 'Cette contribution a été retirée. Créez une nouvelle publication pour partager à nouveau votre texte.');
    }
}

/* R13-I — normalisation de reprise : une durée impossible ne doit jamais
 * alimenter Mon ITHAKYA, et une horloge du terminal en avance ne doit pas
 * bloquer les reprises sur un deuxième appareil. Le serveur fait autorité sur
 * les dates futures ; les dates antérieures restent utiles pour ordonner les
 * requêtes arrivées tardivement. Ne touche ni aux points ni aux récompenses. */
function normaliserLecture(mixed $position, mixed $duration, mixed $at, ?int $nowMs = null): array {
    $nowMs ??= (int)round(microtime(true) * 1000);
    if ((!is_int($position) && !is_float($position)) || !is_finite((float)$position)
        || (!is_int($duration) && !is_float($duration)) || !is_finite((float)$duration)
        || $position < 0 || $duration <= 0 || $duration > 36000
        || $position > 36000 || $position > $duration + 1
        || !is_int($at) || $at < 1700000000000) {
        fail(422, 'lecture', 'Cette position de lecture n’est pas valide.');
    }
    /* Une faible tolérance (+1 s) absorbe les écarts de mesure du lecteur. */
    return ['position' => round((float)min($position, $duration), 1),
        'duration' => round((float)$duration, 1),
        'at' => min($at, $nowMs)];
}
/* Accepte une nouvelle reprise si l'ancienne est absente, périmée ou
 * anormalement située dans le futur. À date égale, évite les réécritures. */
/* L20 — Intervalles vus [début, fin] en secondes : liste bornée (≤ 40), triée, fusionnée, arrondie au dixième. */
function normaliserVu(mixed $vu, float $duration): array {
    if (!is_array($vu) || count($vu) > 200) fail(422, 'lecture', 'Les intervalles de lecture ne sont pas valides.');
    $out = [];
    foreach ($vu as $r) {
        if (!is_array($r) || count($r) !== 2 || !is_numeric($r[0] ?? null) || !is_numeric($r[1] ?? null)) fail(422, 'lecture', 'Les intervalles de lecture ne sont pas valides.');
        $a = max(0.0, (float)$r[0]); $b = min($duration, (float)$r[1]);
        if (!is_finite($a) || !is_finite($b)) fail(422, 'lecture', 'Les intervalles de lecture ne sont pas valides.');
        if ($b > $a) $out[] = [round($a, 1), round($b, 1)];
    }
    return fusionnerVu([], $out);
}
function fusionnerVu(array $a, array $b): array {
    $all = array_values(array_filter(array_merge($a, $b), fn($r) => is_array($r) && count($r) === 2 && $r[1] > $r[0]));
    usort($all, fn($x, $y) => $x[0] <=> $y[0]);
    $m = [];
    foreach ($all as $r) {
        $n = count($m);
        if ($n && $r[0] <= $m[$n - 1][1] + 0.5) $m[$n - 1][1] = max($m[$n - 1][1], $r[1]); else $m[] = [$r[0], $r[1]];
    }
    while (count($m) > 40) {  /* borne de taille : retrait de l'intervalle le plus court (la couverture ne peut qu'être sous-estimée) */
        $short = 0; foreach ($m as $i => $r) if ($r[1] - $r[0] < $m[$short][1] - $m[$short][0]) $short = $i;
        array_splice($m, $short, 1);
    }
    return $m;
}
function remplacerLecture(?array $ancienne, array $nouvelle, int $nowMs): bool {
    if ($ancienne === null) return true;
    $oldAt = $ancienne['at'] ?? null;
    if (!is_int($oldAt)) return true;
    return $oldAt > $nowMs || $oldAt < $nouvelle['at'];
}
function throttle(PDO $db, string $scope, string $subject, int $limit, int $seconds, array $config): void {
    /* Recette locale uniquement : les limites peuvent être multipliées (clé limites_recette) pour enchaîner toutes les recettes
     * depuis la même adresse. Sans effet en production : la clé est ignorée hors environnement « local ». */
    if (($config['environment'] ?? '') === 'local' && is_int($config['limites_recette'] ?? null) && $config['limites_recette'] > 1) $limit *= min(50, $config['limites_recette']);
    $now = time();
    $bucket = (int)floor($now / $seconds);
    $key = hash_hmac('sha256', $scope . ':' . $subject . ':' . $bucket, $config['password_pepper']);
    /* Atomic counter; no plaintext IP address is retained. */
    if (driver($db) === 'mysql') {
        dbQuery($db, 'INSERT INTO itp_limits (limit_key, hits, expires_at) VALUES (?, 1, ?) ON DUPLICATE KEY UPDATE hits = hits + 1', [$key, ($bucket + 1) * $seconds]);
    } else {
        dbQuery($db, 'INSERT INTO itp_limits (limit_key, hits, expires_at) VALUES (?, 1, ?) ON CONFLICT(limit_key) DO UPDATE SET hits = hits + 1', [$key, ($bucket + 1) * $seconds]);
    }
    $hits = (int)dbQuery($db, 'SELECT hits FROM itp_limits WHERE limit_key = ?', [$key])->fetchColumn();
    if ($hits > $limit) {
        header('Retry-After: ' . max(1, ($bucket + 1) * $seconds - $now));
        fail(429, 'rate_limit', 'Trop de tentatives. Réessayez un peu plus tard.');
    }
    /* TECH-02 : purge espacée (1 appel sur 50). Sans index sur expires_at, la purge à chaque appel parcourt toute la table :
     * mesuré à 209 ms par appel pour 100 000 lignes (8 accès simultanés), contre 0,6 ms purge espacée. Les lignes expirées restent
     * seulement un peu plus longtemps ; la limite elle-même ne dépend que de la clé du créneau en cours. */
    if (random_int(1, 50) === 1) dbQuery($db, 'DELETE FROM itp_limits WHERE expires_at < ?', [$now - 3600]);
}

/* ---------- Configuration et stockage (partagés avec les outils privés) ---------- */

function loadConfig(string $path, string $webRoot): array {
    $real = realpath($path);
    $web = realpath($webRoot);
    if (!$real || !$web || str_starts_with($real, $web . DIRECTORY_SEPARATOR)) {
        fail(503, 'not_configured', 'Les comptes ne sont pas encore disponibles sur cette installation privée. La découverte reste accessible.');
    }
    $config = require $real;
    if (!is_array($config) || !in_array($config['environment'] ?? '', ['local', 'production'], true)
        || !is_string($config['password_pepper'] ?? null) || strlen($config['password_pepper']) < 64
        || !is_string($config['bootstrap_invitation'] ?? null) || strlen($config['bootstrap_invitation']) < 32) {
        fail(503, 'not_configured', 'Les comptes ne sont pas encore disponibles sur cette installation privée. La découverte reste accessible.');
    }
    $private = realpath(dirname($real));
    if (!$private || str_starts_with($private . DIRECTORY_SEPARATOR, $web . DIRECTORY_SEPARATOR)) {
        fail(503, 'configuration', 'Le stockage privé doit rester séparé.');
    }
    $config['_private'] = $private;
    $config['_web'] = $web;
    return $config;
}
function openDatabase(array $config): PDO {
    $database = $config['database'] ?? [];
    $kind = $database['driver'] ?? '';
    if ($kind === 'sqlite' && $config['environment'] === 'local') {
        $db = new PDO('sqlite:' . $config['_private'] . '/pilot.sqlite');
        $db->exec('PRAGMA foreign_keys=ON');
        $db->exec('PRAGMA busy_timeout=5000');
    } elseif ($kind === 'mysql') {
        $host = $database['host'] ?? '';
        $name = $database['name'] ?? '';
        // L20 : port facultatif (défaut 3306 inchangé). Les bases OVH « Web Cloud Databases » utilisent un port dédié.
        $port = $database['port'] ?? 3306;
        if (is_string($port) && preg_match('/^[0-9]{1,5}$/D', $port)) $port = (int)$port;
        if (!preg_match('/^[a-zA-Z0-9.-]+$/D', $host) || !preg_match('/^[a-zA-Z0-9_]+$/D', $name)
            || !is_int($port) || $port < 1 || $port > 65535) {
            fail(503, 'configuration', 'Le pilote privé attend sa configuration.');
        }
        $db = new PDO('mysql:host=' . $host . ';port=' . $port . ';dbname=' . $name . ';charset=utf8mb4',
            $database['user'] ?? '', $database['password'] ?? '', [PDO::ATTR_EMULATE_PREPARES => false]);
    } else {
        fail(503, 'configuration', 'Le pilote privé attend sa configuration.');
    }
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    return $db;
}
/* Tables par version de schéma. La v1 est celle du pilote Signature du 17 octobre 2026. */
function schemaTables(string $kind, int $version): array {
    $tables = [
        'itp_meta' => '(name VARCHAR(80) PRIMARY KEY, value TEXT NOT NULL)',
        'itp_users' => '(id VARCHAR(32) PRIMARY KEY, login VARCHAR(40) NOT NULL UNIQUE, display_name VARCHAR(80) NOT NULL, password_hash VARCHAR(255) NOT NULL, avatar VARCHAR(16) NOT NULL, interests TEXT NOT NULL, role VARCHAR(16) NOT NULL, auth_version INTEGER NOT NULL DEFAULT 1, created_at BIGINT NOT NULL)',
        'itp_invites' => '(token_hash VARCHAR(64) PRIMARY KEY, role VARCHAR(16) NOT NULL, created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL, used_at BIGINT NULL, used_by VARCHAR(32) NULL)',
        'itp_entries' => $version >= 2
            ? '(id VARCHAR(32) PRIMARY KEY, user_id VARCHAR(32) NOT NULL, parent_id VARCHAR(32) NULL, body TEXT NOT NULL, created_at BIGINT NOT NULL, removed_at BIGINT NULL, request_key VARCHAR(64) NOT NULL, body_hash VARCHAR(64) NOT NULL, context_id VARCHAR(16) NOT NULL DEFAULT \'signature\', chapter SMALLINT NULL, UNIQUE(user_id, request_key), FOREIGN KEY(user_id) REFERENCES itp_users(id), FOREIGN KEY(parent_id) REFERENCES itp_entries(id))'
            : '(id VARCHAR(32) PRIMARY KEY, user_id VARCHAR(32) NOT NULL, parent_id VARCHAR(32) NULL, body TEXT NOT NULL, created_at BIGINT NOT NULL, removed_at BIGINT NULL, request_key VARCHAR(64) NOT NULL, body_hash VARCHAR(64) NOT NULL, UNIQUE(user_id, request_key), FOREIGN KEY(user_id) REFERENCES itp_users(id), FOREIGN KEY(parent_id) REFERENCES itp_entries(id))',
        'itp_progress' => '(user_id VARCHAR(32) PRIMARY KEY, data TEXT NOT NULL, updated_at BIGINT NOT NULL, FOREIGN KEY(user_id) REFERENCES itp_users(id))',
        'itp_limits' => '(limit_key VARCHAR(64) PRIMARY KEY, hits INTEGER NOT NULL, expires_at BIGINT NOT NULL)',
    ];
    if ($version >= 2) {
        $tables['itp_progress2'] = '(user_id VARCHAR(32) NOT NULL, context_id VARCHAR(16) NOT NULL, data TEXT NOT NULL, updated_at BIGINT NOT NULL, PRIMARY KEY(user_id, context_id), FOREIGN KEY(user_id) REFERENCES itp_users(id))';
        $tables['itp_reads'] = '(user_id VARCHAR(32) NOT NULL, context_id VARCHAR(16) NOT NULL, seen_at BIGINT NOT NULL, PRIMARY KEY(user_id, context_id), FOREIGN KEY(user_id) REFERENCES itp_users(id))';
    }
    if ($version >= 3) {
        /* Jetons de récupération : code personnel (kind = code) ou lien émis par l'administrateur (kind = link). Seule l'empreinte est conservée. */
        $tables['itp_recovery'] = '(token_hash VARCHAR(64) PRIMARY KEY, user_id VARCHAR(32) NOT NULL, kind VARCHAR(8) NOT NULL, created_at BIGINT NOT NULL, expires_at BIGINT NOT NULL, used_at BIGINT NULL, FOREIGN KEY(user_id) REFERENCES itp_users(id))';
        /* États de parcours transversaux (Grande Traversée), un document JSON validé par clé. */
        $tables['itp_states'] = '(user_id VARCHAR(32) NOT NULL, state_key VARCHAR(24) NOT NULL, data TEXT NOT NULL, updated_at BIGINT NOT NULL, PRIMARY KEY(user_id, state_key), FOREIGN KEY(user_id) REFERENCES itp_users(id))';
    }
    if ($version >= 4) {
        /* Signalements : un par compte et par contribution ; décision de l'administrateur (retirée / conservée). */
        $tables['itp_reports'] = '(id VARCHAR(32) PRIMARY KEY, entry_id VARCHAR(32) NOT NULL, reporter_id VARCHAR(32) NOT NULL, reason VARCHAR(24) NOT NULL, created_at BIGINT NOT NULL, status VARCHAR(12) NOT NULL, decided_by VARCHAR(32) NULL, decided_at BIGINT NULL, UNIQUE(entry_id, reporter_id), FOREIGN KEY(entry_id) REFERENCES itp_entries(id), FOREIGN KEY(reporter_id) REFERENCES itp_users(id))';
    }
    if ($version >= 5) {
        /* M2 : progression par œuvre. universe_id est recopié du registre au moment de l'écriture (requêtes par univers). */
        $tables['itp_work_progress'] = '(user_id VARCHAR(32) NOT NULL, work_id VARCHAR(64) NOT NULL, universe_id VARCHAR(16) NOT NULL, data TEXT NOT NULL, updated_at BIGINT NOT NULL, PRIMARY KEY(user_id, work_id), FOREIGN KEY(user_id) REFERENCES itp_users(id))';
        /* Installation neuve : colonne work_id directement dans itp_entries (une base migrée la reçoit par ALTER TABLE ADD COLUMN). */
        $tables['itp_entries'] = '(id VARCHAR(32) PRIMARY KEY, user_id VARCHAR(32) NOT NULL, parent_id VARCHAR(32) NULL, body TEXT NOT NULL, created_at BIGINT NOT NULL, removed_at BIGINT NULL, request_key VARCHAR(64) NOT NULL, body_hash VARCHAR(64) NOT NULL, context_id VARCHAR(16) NOT NULL DEFAULT \'signature\', chapter SMALLINT NULL, work_id VARCHAR(64) NULL, UNIQUE(user_id, request_key), FOREIGN KEY(user_id) REFERENCES itp_users(id), FOREIGN KEY(parent_id) REFERENCES itp_entries(id))';
    }
    if ($version >= 6) {
        /* L'ancienne table itp_reads reste intacte pour un retour à l'API v5.
         * Le fil et les notifications v6 n'utilisent que ces reçus précis. */
        $tables['itp_thread_reads'] = '(user_id VARCHAR(32) NOT NULL, thread_id VARCHAR(32) NOT NULL, work_id VARCHAR(64) NOT NULL, seen_at BIGINT NOT NULL, PRIMARY KEY(user_id, thread_id), FOREIGN KEY(user_id) REFERENCES itp_users(id), FOREIGN KEY(thread_id) REFERENCES itp_entries(id))';
    }
    $end = $kind === 'mysql' ? ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin' : '';
    return array_map(fn(string $definition): string => $definition . $end, $tables);
}
function createTables(PDO $db, int $version): void {
    foreach (schemaTables(driver($db), $version) as $table => $definition) {
        $db->exec('CREATE TABLE IF NOT EXISTS ' . $table . ' ' . $definition);
    }
    if ($version >= 2 && !indexExists($db, 'itp_entries', 'itp_entries_context')) {
        $db->exec('CREATE INDEX itp_entries_context ON itp_entries (context_id, parent_id, created_at)');
    }
    if ($version >= 5 && !indexExists($db, 'itp_entries', 'itp_entries_work')) {
        $db->exec('CREATE INDEX itp_entries_work ON itp_entries (work_id, parent_id, created_at)');
    }
}
function indexExists(PDO $db, string $table, string $index): bool {
    if (driver($db) === 'mysql') {
        return (bool)dbQuery($db, 'SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND INDEX_NAME = ?', [$table, $index])->fetchColumn();
    }
    return (bool)dbQuery($db, "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND tbl_name = ? AND name = ?", [$table, $index])->fetchColumn();
}
function metaValue(PDO $db, string $name): ?string {
    $value = dbQuery($db, 'SELECT value FROM itp_meta WHERE name = ?', [$name])->fetchColumn();
    return $value === false ? null : (string)$value;
}
function schemaNeedsInstallation(PDO $db): bool {
    // Une seule lecture : les deux marqueurs deviennent visibles ensemble à la validation de la transaction.
    $markers = dbQuery($db, "SELECT name, value FROM itp_meta WHERE name IN ('schema_version', 'bootstrap_v1')")->fetchAll(PDO::FETCH_KEY_PAIR);
    $version = $markers['schema_version'] ?? null;
    if ($version === (string)ITP_SCHEMA) return false;
    /* Base existante : migration privée explicite, jamais automatique à la première requête. */
    if (in_array($version, ['2', '3', '4', '5'], true)) fail(503, 'migration_required', 'Les comptes sont en cours de mise à jour. Vous pouvez continuer à explorer librement.');
    if ($version !== null) fail(503, 'schema', 'Les comptes sont momentanément indisponibles. La découverte reste accessible.');
    if (isset($markers['bootstrap_v1'])) fail(503, 'migration_required', 'Les comptes sont en cours de mise à jour. Vous pouvez continuer à explorer librement.');
    return true;
}
/* Une base v1 existante reste du ressort de l'outil de migration privé. */
function ensureSchema(PDO $db, array $config): void {
    $kind = driver($db);
    // A provisioned application account only reads the schema markers.
    try { if (!schemaNeedsInstallation($db)) return; }
    catch (PDOException $e) {
        $missing = (string)$e->getCode() === '42S02'
            || ($kind === 'sqlite' && str_contains($e->getMessage(), 'no such table: itp_meta'));
        if (!$missing) throw $e;
        $db->exec('CREATE TABLE IF NOT EXISTS itp_meta ' . schemaTables($kind, ITP_SCHEMA)['itp_meta']);
    }
    if ($kind !== 'mysql') {
        installEmptySchema($db, $config);
        return;
    }
    // MariaDB/MySQL : le même verrou par base protège le DDL et l'invitation d'amorçage.
    $database = (string)dbQuery($db, 'SELECT DATABASE()')->fetchColumn();
    $lock = 'ithakya:schema:' . substr(hash('sha256', $database), 0, 40);
    if ((int)dbQuery($db, 'SELECT GET_LOCK(?, 15)', [$lock])->fetchColumn() !== 1) {
        if (!schemaNeedsInstallation($db)) return;
        throw new RuntimeException('Verrou d’amorçage indisponible.');
    }
    try {
        if (schemaNeedsInstallation($db)) installEmptySchema($db, $config);
    } finally {
        dbQuery($db, 'SELECT RELEASE_LOCK(?)', [$lock])->fetchColumn();
    }
}
function installEmptySchema(PDO $db, array $config): void {
    createTables($db, ITP_SCHEMA);
    $db->beginTransaction();
    try {
        dbQuery($db, 'INSERT INTO itp_meta (name, value) VALUES (?, ?)', ['bootstrap_v1', 'installed']);
        dbQuery($db, 'INSERT INTO itp_meta (name, value) VALUES (?, ?)', ['schema_version', (string)ITP_SCHEMA]);
        dbQuery($db, 'INSERT INTO itp_invites (token_hash, role, created_at, expires_at) VALUES (?, ?, ?, ?)',
            [hash('sha256', $config['bootstrap_invitation']), 'admin', time(), time() + 604800]);
        $db->commit();
    } catch (PDOException $e) {
        if ($db->inTransaction()) $db->rollBack();
        if (!in_array((string)$e->getCode(), ['23000', '23505'], true)) throw $e;
        if (metaValue($db, 'schema_version') !== (string)ITP_SCHEMA) throw $e;
    }
}

/* ---------- Données par univers ---------- */

function context(mixed $value, ?array $user = null): string {
    if (!is_string($value) || !array_key_exists($value, ITP_CONTEXTS)) fail(422, 'context', 'Cet univers n’est pas reconnu.');
    if (in_array($value, ITP_PARTNER_CONTEXTS, true) && !isPartner($user)) fail(403, 'partner_required', 'Cet espace est réservé aux partenaires autorisés.');
    return $value;
}
function emptyProgress(): array {
    return ['steps' => (object)[], 'saved' => false, 'note_k' => null, 'idea' => null];
}
function currentProgress(PDO $db, string $user, string $ctx): array {
    $raw = dbQuery($db, 'SELECT data FROM itp_progress2 WHERE user_id = ? AND context_id = ?', [$user, $ctx])->fetchColumn();
    $data = $raw ? json_decode($raw, true, 16, JSON_THROW_ON_ERROR) : [];
    return ['steps' => $data['steps'] ?? [], 'saved' => $data['saved'] ?? false, 'note_k' => $data['note_k'] ?? null, 'idea' => $data['idea'] ?? null, 'quiz' => $data['quiz'] ?? null, 'credit_review' => $data['credit_review'] ?? []];
}
function saveProgress(PDO $db, string $user, string $ctx, array $data): void {
    $json = json_encode($data, JSON_THROW_ON_ERROR);
    if (driver($db) === 'mysql') {
        dbQuery($db, 'INSERT INTO itp_progress2 (user_id, context_id, data, updated_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = VALUES(updated_at)', [$user, $ctx, $json, time()]);
    } else {
        dbQuery($db, 'INSERT INTO itp_progress2 (user_id, context_id, data, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, context_id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at', [$user, $ctx, $json, time()]);
    }
}
/* ---------- M2 — registre des œuvres (catalogue publié, champ « oeuvres ») ---------- */

/* Le catalogue publié fait foi. Une entrée invalide est ignorée (journal serveur), jamais devinée :
 * identifiant hors format ou déjà pris, univers inconnu, statut inconnu, nombre d'idées ≠ 5 tant que M1 n'est pas
 * arbitré, durée absente, ou média déjà déclaré par une autre œuvre (empêche un double gain par duplication). */
function itpCatalogueData(array $config): array {
    static $cache = [];
    $file = ($config['_web'] ?? '') . '/assets/data/catalogue.json';
    if (!array_key_exists($file, $cache)) {
        $data = is_file($file) ? json_decode((string)file_get_contents($file), true) : null;
        $cache[$file] = is_array($data) ? $data : [];
    }
    return $cache[$file];
}
/* Territoires d'une œuvre : liste sans doublon de territoires connus, le premier étant le principal. Pour une œuvre nouvelle, le
 * contexte technique de l'œuvre est obligatoirement celui de son territoire principal. Œuvre historique sans déclaration valide :
 * rattachement par défaut (ITP_LEGACY_TERRITOIRES). Retourne null si la déclaration est invalide. */
function itpWorkTerritoires(array $w, string $ctx, bool $legacy): ?array {
    $defaut = isset(ITP_LEGACY_TERRITOIRES[$ctx]) ? [ITP_LEGACY_TERRITOIRES[$ctx]] : [];   /* Retail : espace partenaire, aucun territoire public */
    $t = $w['territoires'] ?? null;
    if ($t === null) return $legacy ? $defaut : null;
    if (!is_array($t) || !array_is_list($t) || !$t || count($t) !== count(array_unique($t)) || count($t) > 5) return $legacy ? $defaut : null;
    foreach ($t as $x) if (!is_string($x) || !array_key_exists($x, ITP_TERRITOIRES)) return $legacy ? $defaut : null;
    if ($legacy && $ctx === 'retail') return [];
    if (!$legacy && ITP_TERRITOIRES[$t[0]] !== $ctx) return null;
    return $t;
}
function itpWorks(array $config): array {
    static $cache = [];
    $key = ($config['_web'] ?? '') . '|' . (($config['oeuvres_essai_prive'] ?? false) === true ? 'e' : '-');
    if (isset($cache[$key])) return $cache[$key];
    $cat = itpCatalogueData($config);
    $contenus = [];
    foreach ((array)($cat['contenus'] ?? []) as $c) if (is_array($c) && is_string($c['id'] ?? null)) $contenus[$c['id']] = $c;
    $declared = [];
    foreach ((array)($cat['oeuvres'] ?? []) as $w) if (is_array($w) && is_string($w['id'] ?? null) && !isset($declared[$w['id']])) $declared[$w['id']] = $w;
    $works = []; $medias = [];
    $build = function (string $id, string $u, array $w, bool $legacy, string $courtId, string $longId) use (&$works, &$medias, $contenus, $config): void {
        $court = $contenus[$courtId] ?? []; $long = $contenus[$longId] ?? [];
        $idees = $legacy ? ITP_CONTEXTS[$u] : ($w['idees'] ?? null);
        $quiz = $legacy ? ITP_QUIZ[$u] : (array_key_exists('quiz_bonne', $w) ? $w['quiz_bonne'] : (($long['quiz']['bonne'] ?? null)));
        $statut = $legacy ? 'disponible' : ($w['statut'] ?? null);
        $dc = is_numeric($court['duree_s'] ?? null) ? (float)$court['duree_s'] : null; $dl = is_numeric($long['duree_s'] ?? null) ? (float)$long['duree_s'] : null;
        $reject = null;
        if (!$legacy && (!preg_match(ITP_WORK_ID, $id) || in_array($id, ITP_LEGACY_WORKS, true))) $reject = 'identifiant';
        elseif (!$legacy && !in_array($statut, ITP_WORK_STATUSES, true)) $reject = 'statut';
        elseif (!is_int($idees) || $idees < 1 || $idees > 12 || (!ITP_M1_IDEES_VARIABLES && $idees !== 5)) $reject = 'idees (M1 non arbitré : 5)';
        elseif ($quiz !== null && (!is_int($quiz) || $quiz < 0 || $quiz > 2)) $reject = 'quiz';
        elseif (!$legacy && (!$dc || $dc <= 0 || !$dl || $dl <= 0)) $reject = 'durees';
        elseif (!$legacy && (($court['oeuvre'] ?? null) !== $id || ($long['oeuvre'] ?? null) !== $id)) $reject = 'contenus';
        $terr = itpWorkTerritoires($w, $u, $legacy);
        if (!$reject && $terr === null) $reject = 'territoires';
        foreach ([$court, $long] as $c) {
            $m = $c['media_sha256'] ?? ($c['media'] ?? null);
            if (!$reject && is_string($m) && $m !== '' && isset($medias[$m]) && $medias[$m] !== $id) $reject = 'media deja declare par ' . $medias[$m];
        }
        if ($reject) { error_log('ITHAKYA pilot: oeuvre ignoree (' . $id . ') : ' . $reject); return; }
        if (!$legacy && $statut === 'essai_prive' && (($config['oeuvres_essai_prive'] ?? false) !== true)) return;
        foreach ([$court, $long] as $c) { $m = $c['media_sha256'] ?? ($c['media'] ?? null); if (is_string($m) && $m !== '') $medias[$m] = $id; }
        $works[$id] = ['id' => $id, 'universe' => $u, 'legacy' => $legacy, 'statut' => $statut, 'idees' => $idees, 'quiz' => $quiz,
            'court' => $courtId, 'long' => $longId, 'court_s' => $dc, 'long_s' => $dl, 'territoires' => $terr, 'titre' => (string)($w['titre'] ?? ($court['titre'] ?? $id))];
    };
    foreach (ITP_LEGACY_WORKS as $u => $id) $build($id, $u, $declared[$id] ?? [], true, $u . '.court', $u . '.long');
    foreach ($declared as $id => $w) {
        if (in_array($id, ITP_LEGACY_WORKS, true)) continue;
        $u = $w['univers'] ?? null;
        if (!is_string($u) || !array_key_exists($u, ITP_CONTEXTS)) { error_log('ITHAKYA pilot: oeuvre ignoree (' . $id . ') : univers'); continue; }
        $build($id, $u, $w, false, $id . '.court', $id . '.long');
    }
    return $cache[$key] = $works;
}
/* Œuvre demandée par une requête : existante, univers accessible au compte (Retail réservé aux partenaires),
 * écriture refusée sur une œuvre retirée. */
function itpWork(array $config, mixed $id, ?array $user, bool $write = false): array {
    $works = itpWorks($config);
    if (!is_string($id) || !isset($works[$id])) fail(422, 'work', 'Cette œuvre n’est pas reconnue.');
    $w = $works[$id];
    context($w['universe'], $user);
    if ($write && $w['statut'] === 'retiree') fail(409, 'work_retired', 'Cette œuvre a été retirée : votre parcours reste consultable, il n’est plus complété.');
    return $w;
}
function itpLegacyWork(array $config, string $ctx): array {
    $id = ITP_LEGACY_WORKS[$ctx] ?? null; $works = itpWorks($config);
    if ($id === null || !isset($works[$id])) fail(422, 'work_required', 'Cet univers ne propose que des œuvres déclarées : précisez l’œuvre.');
    return $works[$id];
}
/* Œuvre d'une contribution : NULL (contributions antérieures à v5) = œuvre historique de l'univers. */
function itpEntryWork(?string $workId, string $ctx): ?string { return $workId ?? (ITP_LEGACY_WORKS[$ctx] ?? null); }
/* Contenus lisibles dont la position peut être gardée : Court et Long des œuvres du registre. */
function itpWorkContent(array $config, string $content): ?array {
    foreach (itpWorks($config) as $w) { if ($w['court'] === $content) return [$w, 'court']; if ($w['long'] === $content) return [$w, 'long']; }
    return null;
}
function currentWorkProgress(PDO $db, string $user, array $work): array {
    $raw = dbQuery($db, 'SELECT data FROM itp_work_progress WHERE user_id = ? AND work_id = ?', [$user, $work['id']])->fetchColumn();
    /* Œuvre historique sans ligne v5 (base migrée partiellement) : lecture de la ligne v4, jamais réécrite à l'identique sans événement. */
    if ($raw === false && $work['legacy']) return currentProgress($db, $user, $work['universe']);
    $data = $raw ? json_decode($raw, true, 16, JSON_THROW_ON_ERROR) : [];
    return ['steps' => $data['steps'] ?? [], 'saved' => $data['saved'] ?? false, 'note_k' => $data['note_k'] ?? null, 'idea' => $data['idea'] ?? null, 'quiz' => $data['quiz'] ?? null, 'credit_review' => $data['credit_review'] ?? []];
}
function saveWorkProgress(PDO $db, string $user, array $work, array $data): void {
    $json = json_encode($data, JSON_THROW_ON_ERROR);
    if (driver($db) === 'mysql') {
        dbQuery($db, 'INSERT INTO itp_work_progress (user_id, work_id, universe_id, data, updated_at) VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), universe_id = VALUES(universe_id), updated_at = VALUES(updated_at)', [$user, $work['id'], $work['universe'], $json, time()]);
    } else {
        dbQuery($db, 'INSERT INTO itp_work_progress (user_id, work_id, universe_id, data, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, work_id) DO UPDATE SET data = excluded.data, universe_id = excluded.universe_id, updated_at = excluded.updated_at', [$user, $work['id'], $work['universe'], $json, time()]);
    }
    /* Écriture double de l'œuvre historique : la ligne v4 reste l'image exacte (retour arrière sans perte). */
    if ($work['legacy']) saveProgress($db, $user, $work['universe'], $data);
}
/* Parcours par œuvre du compte (Mon ITHAKYA, programmation). Positions de lecture : état « lecture », par contenu. */
function itpWorksSummary(PDO $db, array $config, array $user): array {
    $allowed = allowedContexts($user); $rows = [];
    foreach (dbQuery($db, 'SELECT work_id, data, updated_at FROM itp_work_progress WHERE user_id = ?', [$user['id']])->fetchAll() as $r) $rows[$r['work_id']] = $r;
    $contrib = [];
    foreach (dbQuery($db, 'SELECT context_id, work_id, COUNT(*) AS n FROM itp_entries WHERE user_id = ? AND removed_at IS NULL GROUP BY context_id, work_id', [$user['id']])->fetchAll() as $r) {
        if (!array_key_exists($r['context_id'], ITP_CONTEXTS)) continue;
        $k = itpEntryWork($r['work_id'], $r['context_id']); if ($k === null) continue; $contrib[$k] = ($contrib[$k] ?? 0) + (int)$r['n'];
    }
    $out = [];
    foreach (itpWorks($config) as $id => $w) {
        if (!in_array($w['universe'], $allowed, true)) continue;
        $p = isset($rows[$id]) ? json_decode($rows[$id]['data'], true, 16, JSON_THROW_ON_ERROR) : ($w['legacy'] ? currentProgress($db, $user['id'], $w['universe']) : []);
        $out[] = ['oeuvre' => $id, 'univers' => $w['universe'], 'historique' => $w['legacy'], 'statut' => $w['statut'], 'titre' => $w['titre'], 'territoires' => $w['territoires'],
            'idees' => $w['idees'], 'court' => $w['court'], 'long' => $w['long'], 'steps' => (object)($p['steps'] ?? []), 'saved' => (bool)($p['saved'] ?? false),
            'note_k' => $p['note_k'] ?? null, 'idea' => $p['idea'] ?? null, 'quiz_answered' => is_array($p['quiz'] ?? null),
            'credit_review' => itpCreditPublic($p['credit_review'] ?? []), 'contributions' => $contrib[$id] ?? 0, 'updated_at' => isset($rows[$id]) ? (int)$rows[$id]['updated_at'] : null];
    }
    return $out;
}
/* Repères réels par univers : aucune valeur de XP, Points ou Grade n'est calculée ici. */
function accountSummary(PDO $db, string $user, ?array $account = null): array {
    $summary = [];
    foreach (allowedContexts($account) as $ctx) {
        $summary[$ctx] = ['steps' => (object)[], 'saved' => false, 'note_k' => null, 'idea' => null, 'contributions' => 0, 'contribution' => false, 'collective' => false, 'unread' => 0];
    }
    foreach (dbQuery($db, 'SELECT context_id, data FROM itp_progress2 WHERE user_id = ?', [$user])->fetchAll() as $row) {
        if (!isset($summary[$row['context_id']])) continue;
        $data = json_decode($row['data'], true, 16, JSON_THROW_ON_ERROR);
        $summary[$row['context_id']]['steps'] = (object)($data['steps'] ?? []);
        $summary[$row['context_id']]['saved'] = (bool)($data['saved'] ?? false);
        $summary[$row['context_id']]['note_k'] = $data['note_k'] ?? null;
        $summary[$row['context_id']]['idea'] = $data['idea'] ?? null;
        $summary[$row['context_id']]['quiz'] = $data['quiz'] ?? null;
        $summary[$row['context_id']]['credit_review'] = itpCreditPublic($data['credit_review'] ?? []);
    }
    foreach (dbQuery($db, 'SELECT context_id, COUNT(*) AS n FROM itp_entries WHERE user_id = ? AND removed_at IS NULL GROUP BY context_id', [$user])->fetchAll() as $row) {
        if (!isset($summary[$row['context_id']])) continue;
        $summary[$row['context_id']]['contributions'] = (int)$row['n'];
        $summary[$row['context_id']]['contribution'] = (int)$row['n'] > 0;
    }
    /* Collectif : une réponse non retirée échangée entre deux comptes distincts, dans un sens ou dans l'autre. */
    $collective = dbQuery($db, 'SELECT DISTINCT r.context_id FROM itp_entries r JOIN itp_entries t ON t.id = r.parent_id
        WHERE r.removed_at IS NULL AND t.removed_at IS NULL AND r.context_id = t.context_id
          AND ((r.user_id = ? AND t.user_id <> ?) OR (t.user_id = ? AND r.user_id <> ?))', [$user, $user, $user, $user])->fetchAll();
    foreach ($collective as $row) if (isset($summary[$row['context_id']])) $summary[$row['context_id']]['collective'] = true;
    /* Nouvelles réponses par discussion, jamais par ancien contexte partagé. */
    $unread = dbQuery($db, 'SELECT r.context_id, COUNT(*) AS n FROM itp_entries r JOIN itp_entries t ON t.id = r.parent_id
        LEFT JOIN itp_thread_reads s ON s.user_id = ? AND s.thread_id = t.id
        WHERE r.removed_at IS NULL AND r.user_id <> ? AND r.created_at > COALESCE(s.seen_at, 0)
          AND (t.user_id = ? OR EXISTS (SELECT 1 FROM itp_entries m WHERE m.parent_id = t.id AND m.user_id = ? AND m.created_at <= r.created_at))
        GROUP BY r.context_id', [$user, $user, $user, $user])->fetchAll();
    foreach ($unread as $row) if (isset($summary[$row['context_id']])) $summary[$row['context_id']]['unread'] = (int)$row['n'];
    return $summary;
}
function entryData(array $row, array $viewer): array {
    return ['id' => $row['id'], 'parent_id' => $row['parent_id'], 'context' => $row['context_id'],
        'oeuvre' => array_key_exists($row['context_id'], ITP_CONTEXTS) ? itpEntryWork($row['work_id'] ?? null, $row['context_id']) : null,
        'chapter' => $row['chapter'] === null ? null : (int)$row['chapter'],
        'body' => $row['removed_at'] ? '' : $row['body'], 'removed' => (bool)$row['removed_at'],
        'moderated' => (bool)($row['moderated'] ?? false), 'created_at' => (int)$row['created_at'],
        'author' => ['id' => $row['user_id'], 'display_name' => $row['display_name'], 'avatar' => $row['avatar'], 'avatar_image' => itpAvatarImage($row['avatar'])],
        'can_remove' => $row['user_id'] === $viewer['id'] || $viewer['role'] === 'admin',
        'can_report' => $row['user_id'] !== $viewer['id'] && !$row['removed_at'],
        'reported' => (bool)($row['reported'] ?? false)];
}

/* P4 T8 — Reconnaissance communautaire (« Utile », « Éclairant ») : une reconnaissance par membre, par contribution et par type ;
 * jamais sur sa propre contribution ; aucun crédit de Points ni d'XP (le barème n'est pas modifié). Table créée à la demande (ajout seul, retour : DROP TABLE itp_reactions). */
const ITP_REACTIONS = ['utile', 'eclairant'];
function itpEnsureReactions(PDO $db): void {
    static $ok = false; if ($ok) return;
    dbQuery($db, 'CREATE TABLE IF NOT EXISTS itp_reactions (entry_id VARCHAR(32) NOT NULL, user_id VARCHAR(32) NOT NULL, kind VARCHAR(12) NOT NULL, created_at BIGINT NOT NULL, PRIMARY KEY (entry_id, user_id, kind))');
    $ok = true;
}
function itpReactionsDecorate(PDO $db, array $threads, array $viewer): array {
    $ids = [];
    foreach ($threads as $t) { $ids[] = $t['id']; foreach ($t['replies'] ?? [] as $r) $ids[] = $r['id']; }
    $counts = []; $mine = [];
    if ($ids) {
        itpEnsureReactions($db);
        $pm = implode(',', array_fill(0, count($ids), '?'));
        foreach (dbQuery($db, "SELECT entry_id, kind, COUNT(*) AS n FROM itp_reactions WHERE entry_id IN ($pm) GROUP BY entry_id, kind", $ids)->fetchAll() as $row) $counts[$row['entry_id']][$row['kind']] = (int)$row['n'];
        foreach (dbQuery($db, "SELECT entry_id, kind FROM itp_reactions WHERE user_id = ? AND entry_id IN ($pm)", [$viewer['id'], ...$ids])->fetchAll() as $row) $mine[$row['entry_id']][] = $row['kind'];
    }
    $dec = function (array $e) use ($counts, $mine): array {
        $e['reactions'] = ['utile' => $counts[$e['id']]['utile'] ?? 0, 'eclairant' => $counts[$e['id']]['eclairant'] ?? 0];
        $e['my_reactions'] = $mine[$e['id']] ?? [];
        return $e;
    };
    foreach ($threads as $i => $t) { $r = []; foreach ($t['replies'] ?? [] as $x) $r[] = $dec($x); $t = $dec($t); $t['replies'] = $r; $threads[$i] = $t; }
    return $threads;
}
/* Fil d'un ou plusieurs univers : discussions récentes et leurs réponses (même univers), retraits de modération signalés. */
function feedThreads(PDO $db, array $contexts, array $viewer, int $limit = 40, ?array $work = null, ?array $workIds = null): array {
    $marks = implode(',', array_fill(0, count($contexts), '?'));
    $cols = "e.*, u.display_name, u.avatar,
        EXISTS (SELECT 1 FROM itp_reports m WHERE m.entry_id = e.id AND m.status = 'retiree') AS moderated,
        EXISTS (SELECT 1 FROM itp_reports v WHERE v.entry_id = e.id AND v.reporter_id = ?) AS reported";
    /* M2 : fil d'une seule œuvre (l'œuvre historique reprend aussi les contributions antérieures, work_id NULL). */
    $wsql = ''; $wpar = [];
    if ($work) { $wsql = $work['legacy'] ? ' AND (e.work_id IS NULL OR e.work_id = ?)' : ' AND e.work_id = ?'; $wpar = [$work['id']]; }
    /* S1 : liste d'œuvres (territoire). Les contributions antérieures (work_id NULL) restent celles de l'œuvre historique de leur contexte. */
    if ($workIds !== null) {
        $legacyCtx = array_values(array_filter(array_keys(ITP_LEGACY_WORKS), fn(string $c): bool => in_array(ITP_LEGACY_WORKS[$c], $workIds, true)));
        $wsql = ' AND (e.work_id IN (' . implode(',', array_fill(0, count($workIds), '?')) . ')' . ($legacyCtx ? ' OR (e.work_id IS NULL AND e.context_id IN (' . implode(',', array_fill(0, count($legacyCtx), '?')) . '))' : '') . ')';
        $wpar = [...$workIds, ...$legacyCtx];
    }
    $rows = dbQuery($db, "SELECT $cols FROM itp_entries e JOIN itp_users u ON u.id = e.user_id WHERE e.context_id IN ($marks) AND e.parent_id IS NULL$wsql ORDER BY e.created_at DESC, e.id DESC LIMIT $limit", [$viewer['id'], ...$contexts, ...$wpar])->fetchAll();
    $replies = [];
    if ($rows) {
        $ids = array_column($rows, 'id');
        $pm = implode(',', array_fill(0, count($ids), '?'));
        foreach (dbQuery($db, "SELECT $cols FROM itp_entries e JOIN itp_users u ON u.id = e.user_id WHERE e.parent_id IN ($pm) ORDER BY e.created_at ASC, e.id ASC", [$viewer['id'], ...$ids])->fetchAll() as $reply) {
            if (count($replies[$reply['parent_id']] ?? []) < 80) $replies[$reply['parent_id']][] = entryData($reply, $viewer);
        }
    }
    $threads = [];
    foreach ($rows as $row) { $thread = entryData($row, $viewer); $thread['replies'] = $replies[$row['id']] ?? []; $threads[] = $thread; }
    return itpReactionsDecorate($db, $threads, $viewer);
}

/* Curseurs précis par discussion pour les seuls fils retournés au compte.
 * Ne jamais transmettre les accusés d'autres membres ni les travaux d'autres œuvres. */
function itpFeedSeen(PDO $db, string $user, array $threads): object {
    $ids = array_values(array_unique(array_map(fn(array $t): string => $t['id'], $threads)));
    if (!$ids) return (object)[];
    $marks = implode(',', array_fill(0, count($ids), '?'));
    $rows = dbQuery($db, "SELECT thread_id, seen_at FROM itp_thread_reads WHERE user_id = ? AND thread_id IN ($marks)", [$user, ...$ids])->fetchAll();
    $out = [];
    foreach ($rows as $r) $out[$r['thread_id']] = (int)$r['seen_at'];
    return (object)$out;
}

/* ---------- Progression calculée (v4) ---------- */

function milestone(string $track, int $n): int {
    foreach (ITP_BAREME['ms'][$track] as [$at, $pts]) if ($at === $n) return $pts;
    $list = ITP_BAREME['ms'][$track]; $last = $list[count($list) - 1][0]; $every = ITP_BAREME['ev'][$track];
    return $n > $last && ($n - $last) % $every[0] === 0 ? $every[1] : 0;
}
/* R13 : une simple API « finished » sans lancement ni traces de lecture ne
 * crée plus d'acquis. La mesure du lecteur reste une assertion client, non une
 * preuve anti-fraude ; l'autorité serveur contrôle au moins l'ordre et le temps. */
/* L20 — Durée réelle d'une œuvre, lue dans le catalogue publié (assets/data/catalogue.json, généré depuis la source).
 * Le catalogue fait foi pour les durées et les cinq idées ; il est mis à jour à l'intégration de chaque master AV-05. */
function itpCatalogueDuration(array $config, string $id): ?float {
    static $durations = null;
    if ($durations === null) {
        $durations = [];
        $file = ($config['_web'] ?? '') . '/assets/data/catalogue.json';
        $data = is_file($file) ? json_decode((string)file_get_contents($file), true) : null;
        foreach ((array)($data['contenus'] ?? []) as $c) {
            if (is_array($c) && is_string($c['id'] ?? null) && is_numeric($c['duree_s'] ?? null) && $c['duree_s'] > 0) $durations[$c['id']] = (float)$c['duree_s'];
        }
    }
    return $durations[$id] ?? null;
}
/* L20 — Plancher de fin de Long proportionnel à la durée réelle (décision du 24/10/2026) : temps écoulé depuis le
 * lancement ≥ ratio × durée (ratio 0,9 par défaut, borné entre 0,5 et 1, clé privée long_min_ratio), jamais sous
 * le plancher historique. La couverture transmise par le navigateur reste exigée (≥ 98 %). */
function itpLongFloor(array $config, string $ctx): int {
    $base = ITP_MEDIA_TIMING['long'][$ctx] ?? 40;
    $d = itpCatalogueDuration($config, $ctx . '.long');
    $ratio = is_numeric($config['long_min_ratio'] ?? null) ? max(0.5, min(1.0, (float)$config['long_min_ratio'])) : 0.9;
    return $d ? max($base, (int)floor($ratio * $d)) : $base;
}
/* M2 — même règle (L20), appliquée à la durée réelle du Long de l'œuvre ; plancher historique de l'univers inchangé. */
function itpWorkLongFloor(array $config, array $work): int {
    if ($work['legacy']) return itpLongFloor($config, $work['universe']);
    $base = ITP_MEDIA_TIMING['long'][$work['universe']] ?? 40;
    $ratio = is_numeric($config['long_min_ratio'] ?? null) ? max(0.5, min(1.0, (float)$config['long_min_ratio'])) : 0.9;
    return $work['long_s'] ? max($base, (int)floor($ratio * $work['long_s'])) : $base;
}
function assertPlaybackFinish(array $steps, string $event, mixed $evidence, string $ctx, ?int $at = null, ?int $minSeconds = null): void {
    $kind = str_starts_with($event, 'court_') ? 'court' : 'long';
    $started = $steps[$kind . '_started'] ?? null;
    $now = $at ?? time();
    $floor = max(ITP_MEDIA_TIMING[$kind][$ctx] ?? 40, (int)($minSeconds ?? 0));
    $couvert = is_array($evidence) && array_keys($evidence) === ['coverage'] && is_numeric($evidence['coverage'])
        && (float)$evidence['coverage'] >= .98 && (float)$evidence['coverage'] <= 1;
    if (!is_int($started) || $started > $now || $now - $started < $floor) {
        /* L21 : film entièrement parcouru mais en moins de temps réel que sa durée = lecture accélérée. Règle inchangée
         * (refus) ; seul le motif est précisé : le message générique « poursuivez le film » était faux dans ce cas. */
        if ($couvert && is_int($started) && $started <= $now) {
            fail(409, 'playback_too_fast', 'Ce film a été parcouru plus vite que sa durée réelle : il sera validé lors d’une lecture à vitesse normale. Votre position de lecture est conservée.');
        }
        fail(409, 'playback_unverified', 'Lecture insuffisamment documentée : poursuivez le film avant de confirmer sa fin.');
    }
    if (!$couvert) {
        fail(422, 'playback_evidence', 'La couverture du lecteur est manquante ou invalide. Aucun acquis attribué.');
    }
}
function gradeIndex(int $xp): int { $i = 0; foreach (ITP_GRADES as $n => [$name, $at]) if ($xp >= $at) $i = $n; return $i; }
/* Les acquis sont recalculés à partir des faits enregistrés (étapes horodatées, quiz, première contribution) :
 * une même action répétée, rejouée ou envoyée depuis deux appareils ne crée jamais une seconde ligne. */
function progression(PDO $db, string $userId, ?array $economicConfig = null): array {
    $facts = []; $reviews = [];
    /* M2 : faits lus œuvre par œuvre (itp_work_progress). Une œuvre = une ligne : rejouer la même œuvre, l'ouvrir depuis
     * deux appareils ou par la page d'univers et par sa page propre ne crée jamais un second fait. Les contenus de l'œuvre
     * historique gardent leurs identifiants v4 (« signature.long »), les autres « <œuvre>.long ». Une œuvre retirée du
     * catalogue après coup conserve les acquis déjà enregistrés (aucun retrait rétroactif). */
    $rows = []; $legacyByWork = array_flip(ITP_LEGACY_WORKS);
    foreach (dbQuery($db, 'SELECT work_id, universe_id, data FROM itp_work_progress WHERE user_id = ?', [$userId])->fetchAll() as $row) $rows[$row['work_id']] = $row;
    /* Repli : œuvre historique encore sans ligne v5 (base partiellement migrée) → ligne v4. */
    foreach (dbQuery($db, 'SELECT context_id, data FROM itp_progress2 WHERE user_id = ?', [$userId])->fetchAll() as $row) {
        $w = ITP_LEGACY_WORKS[$row['context_id']] ?? null;
        if ($w !== null && !isset($rows[$w])) $rows[$w] = ['work_id' => $w, 'universe_id' => $row['context_id'], 'data' => $row['data']];
    }
    ksort($rows);
    foreach ($rows as $row) {
        $c = $row['universe_id'];
        if (!in_array($c, ITP_MEMBER_CONTEXTS, true)) continue;
        $d = json_decode($row['data'], true, 16, JSON_THROW_ON_ERROR); $st = $d['steps'] ?? [];
        foreach (($d['credit_review'] ?? []) as $event => $review) {
            $reviews[] = ['oeuvre' => $row['work_id'], 'context' => $c, 'event' => $event,
                ...itpCreditPublic([$event => $review])[$event]];
        }
        $prefix = isset($legacyByWork[$row['work_id']]) ? $c : $row['work_id']; $w = $row['work_id'];
        if (isset($st['court_finished'])) $facts[] = ['at' => (int)$st['court_finished'], 'kind' => 'court', 'context' => $c, 'work' => $w, 'content' => "$prefix.court", 'label' => 'Court vu jusqu’au bout', 'credit_status' => itpCreditStatus($d, 'court_finished')];
        if (isset($st['long_finished'])) $facts[] = ['at' => (int)$st['long_finished'], 'kind' => 'long', 'context' => $c, 'work' => $w, 'content' => "$prefix.long", 'label' => 'Long vu jusqu’au bout', 'credit_status' => itpCreditStatus($d, 'long_finished')];
        if (is_array($d['quiz'] ?? null)) $facts[] = ['at' => (int)$d['quiz']['at'], 'kind' => $d['quiz']['correct'] ? 'quizOk' : 'quiz', 'context' => $c, 'work' => $w, 'content' => "$prefix.long", 'label' => $d['quiz']['correct'] ? 'Quiz : bonne réponse' : 'Quiz : réponse donnée', 'credit_status' => itpCreditStatus($d, 'quiz_answered')];
    }
    $marks = implode(',', array_fill(0, count(ITP_MEMBER_CONTEXTS), '?'));
    /* Une contribution retirée par son auteur ou la modération ne compte pas ; la première contribution effectivement visible de chaque univers compte une fois. */
    foreach (dbQuery($db, "SELECT e.context_id, MIN(e.created_at) AS at FROM itp_entries e WHERE e.user_id = ? AND e.removed_at IS NULL AND e.context_id IN ($marks)
        AND NOT EXISTS (SELECT 1 FROM itp_reports r WHERE r.entry_id = e.id AND r.status = 'retiree') GROUP BY e.context_id", [$userId, ...ITP_MEMBER_CONTEXTS])->fetchAll() as $row) {
        /* Contexte sans œuvre historique (culture, societe) : le fait est rattaché à l'œuvre de la première contribution visible. */
        $qwork = ITP_LEGACY_WORKS[$row['context_id']] ?? dbQuery($db, "SELECT e.work_id FROM itp_entries e WHERE e.user_id = ? AND e.context_id = ? AND e.removed_at IS NULL
            AND NOT EXISTS (SELECT 1 FROM itp_reports r WHERE r.entry_id = e.id AND r.status = 'retiree') ORDER BY e.created_at ASC, e.id ASC LIMIT 1", [$userId, $row['context_id']])->fetchColumn() ?: null;
        $facts[] = ['at' => (int)$row['at'], 'kind' => 'quest', 'context' => $row['context_id'], 'work' => $qwork, 'content' => $row['context_id'] . '.long', 'label' => 'Première contribution dans cet univers'];
    }
    $confirmed = array_values(array_filter($facts, fn(array $f): bool =>
        in_array($f['credit_status'] ?? 'legacy', ['legacy', 'confirmed'], true)));
    $pending = array_values(array_filter($facts, fn(array $f): bool => ($f['credit_status'] ?? '') === 'pending'));
    $result = itpScoreFacts($confirmed);
    $projected = itpScoreFacts([...$confirmed, ...$pending]);
    $result['credit_reviews'] = $reviews;
    $result['pending'] = ['xp' => $projected['xp'] - $result['xp'],
        'points' => $projected['points'] - $result['points'], 'events' => count($pending)];
    // Les Points historiques et les nouveaux Points sont des acquis d'usage.
    // Aucun fait, statut ou repli v4/v5 ne devient un Point convertible.
    $result['points_scope'] = 'usage_non_convertible';
    $result['economic'] = $economicConfig === null ? itpPilotEconomicState() : itpEcoPublic($db,$economicConfig,$userId);
    return $result;
}
function itpScoreFacts(array $facts): array {
    usort($facts, fn($a, $b) => [$a['at'], $a['content'], $a['kind']] <=> [$b['at'], $b['content'], $b['kind']]);
    $xp = 0; $points = 0; $counts = ['long' => 0, 'quiz' => 0, 'quest' => 0]; $universes = []; $journal = [];
    foreach ($facts as $f) {
        $k = $f['kind']; $gx = ITP_BAREME['xp'][$k]; $gp = ITP_BAREME['pts'][$k]; $detail = [];
        $track = ['long' => 'long', 'quiz' => 'quiz', 'quizOk' => 'quiz', 'quest' => 'quest'][$k] ?? null;
        if ($track) { $counts[$track]++; $m = milestone($track, $counts[$track]); if ($m) { $gp += $m; $detail[] = "palier n° {$counts[$track]} : +$m Points"; } }
        if ($k === 'long' && !isset($universes[$f['context']])) { $universes[$f['context']] = true; $gx += ITP_BAREME['xp']['universe']; $detail[] = 'premier Long de l’univers : +' . ITP_BAREME['xp']['universe'] . ' XP'; }
        $g0 = gradeIndex($xp); $g1 = gradeIndex($xp + $gx);
        for ($i = $g0 + 1; $i <= $g1; $i++) { $gp += ITP_BAREME['gradeBonus'][$i]; $detail[] = 'Grade ' . ITP_GRADES[$i][0] . ' : +' . ITP_BAREME['gradeBonus'][$i] . ' Points'; }
        $xp += $gx; $points += $gp;
        $journal[] = ['at' => $f['at'], 'content' => $f['content'], 'context' => $f['context'], 'oeuvre' => $f['work'], 'action' => $k, 'label' => $f['label'], 'xp' => $gx, 'points' => $gp, 'detail' => $detail, 'rule' => ITP_RULES];
    }
    $g = gradeIndex($xp); $next = ITP_GRADES[$g + 1] ?? null;
    return ['xp' => $xp, 'points' => $points, 'grade' => ITP_GRADES[$g][0], 'grade_index' => $g, 'grades' => array_map(fn($x) => ['name' => $x[0], 'xp' => $x[1]], ITP_GRADES),
        'next' => $next ? ['name' => $next[0], 'xp' => $next[1], 'remaining' => $next[1] - $xp] : null, 'journal' => array_reverse($journal), 'rule' => ITP_RULES];
}

/* ATTENZIA (agrégats administrateur) : voir ithakya-attenzia.php (extrait le 07/11/2026, ATZ-04). */

/* Session du pilote, partagée avec la porte de l'espace partenaire (api/ithakya-partenaire.php). */
function startPilotSession(array $config, bool $local): void {
    $private = $config['_private'];
    umask(0077);
    $sessions = $private . '/sessions';
    if (!is_dir($sessions) && !mkdir($sessions, 0700, true) && !is_dir($sessions)) fail(503, 'storage', 'La mémoire du pilote est momentanément indisponible.');
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.gc_maxlifetime', '604800');
    /* TECH-06 : le répertoire de sessions est privé et personnalisé ; sous une configuration de type Debian/Ubuntu (gc_probability = 0),
     * aucun nettoyage ne s'y exécute (mesuré : 300 sessions expirées sur 300 conservées). Collecte explicite, indépendante de la distribution. */
    ini_set('session.gc_probability', '1');
    ini_set('session.gc_divisor', '100');
    /* Nom conservé depuis le pilote Signature : les sessions ouvertes restent valides. */
    session_name('ITHAKYA_SIGNATURE_PILOTE');
    session_save_path($sessions);
    session_set_cookie_params(['lifetime' => 604800, 'path' => '/', 'secure' => !$local, 'httponly' => true, 'samesite' => 'Strict']);
    if (!session_start()) fail(503, 'session', 'La connexion au pilote est momentanément indisponible.');
    if (empty($_SESSION['csrf']) || (isset($_SESSION['rotated_at']) && time() - (int)$_SESSION['rotated_at'] > 120)
        || time() - (int)($_SESSION['last_seen'] ?? 0) > 86400
        || time() - (int)($_SESSION['created_at'] ?? 0) > 604800) resetSession();
    $_SESSION['last_seen'] = time();
}

/* ---------- Récupération de l'accès (v3) ---------- */

/* Code lisible : 6 groupes de 4 caractères sans ambiguïté (≈ 120 bits). Comparaison insensible à la casse, aux espaces et tirets. */
function newRecoveryCode(): string {
    $alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; $groups = [];
    for ($g = 0; $g < 6; $g++) { $part = ''; for ($i = 0; $i < 4; $i++) $part .= $alphabet[random_int(0, strlen($alphabet) - 1)]; $groups[] = $part; }
    return implode('-', $groups);
}
function normalizedCode(string $code): string { return strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $code)); }
function recoveryHash(string $kind, string $secret, array $config): string {
    return hash_hmac('sha256', $kind . ':' . ($kind === 'code' ? normalizedCode($secret) : $secret), $config['password_pepper']);
}
/* Un seul code personnel actif par compte : l'émission d'un nouveau code invalide les précédents. */
function issueRecoveryCode(PDO $db, string $userId, array $config): string {
    $code = newRecoveryCode();
    dbQuery($db, "UPDATE itp_recovery SET used_at = ? WHERE user_id = ? AND kind = 'code' AND used_at IS NULL", [time(), $userId]);
    dbQuery($db, 'INSERT INTO itp_recovery (token_hash, user_id, kind, created_at, expires_at) VALUES (?, ?, ?, ?, ?)',
        [recoveryHash('code', $code, $config), $userId, 'code', time(), time() + 3650 * 86400]);
    return $code;
}
function emptyTraversee(): array { return ['version' => 1, 'chapters' => (object)[], 'choices' => (object)[]]; }
/* Validation stricte : seules les étapes connues, une fin de Long à 98 % minimum, des choix de la liste. */
function cleanTraversee(mixed $data): array {
    if (!is_array($data) || ($data['version'] ?? null) !== 1) fail(422, 'state', 'Cet état de Traversée n’est pas reconnu.');
    $chapters = []; $choices = [];
    $inChapters = $data['chapters'] ?? []; $inChoices = $data['choices'] ?? [];
    if (!is_array($inChapters) || !is_array($inChoices)) fail(422, 'state', 'Cet état de Traversée n’est pas reconnu.');
    foreach ($inChapters as $id => $chapter) {
        if (!array_key_exists($id, ITP_TRAVERSEE) || !is_array($chapter) || ($chapter['completed'] ?? null) !== true) fail(422, 'state', 'Cette étape de la Traversée n’est pas reconnue.');
        $percent = $chapter['playedPercent'] ?? null; $at = $chapter['at'] ?? null;
        if (!is_int($percent) || $percent < 98 || $percent > 100 || !is_int($at) || $at < 1700000000000 || $at > (time() + 86400) * 1000) fail(422, 'state', 'Une étape n’est validée que par une lecture complète du Long.');
        $chapters[$id] = ['completed' => true, 'at' => $at, 'playedPercent' => $percent];
    }
    foreach ($inChoices as $id => $choice) {
        if (!array_key_exists($id, ITP_TRAVERSEE) || !isset($chapters[$id]) || !is_string($choice) || !in_array($choice, ITP_TRAVERSEE[$id], true)) fail(422, 'state', 'Ce choix de regard n’est pas reconnu.');
        $choices[$id] = $choice;
    }
    return ['version' => 1, 'chapters' => $chapters ?: (object)[], 'choices' => $choices ?: (object)[]];
}
function readState(PDO $db, string $user, string $key): array {
    $raw = dbQuery($db, 'SELECT data, updated_at FROM itp_states WHERE user_id = ? AND state_key = ?', [$user, $key])->fetch();
    if (!$raw) return ['data' => emptyTraversee(), 'updated_at' => null];
    return ['data' => json_decode($raw['data'], true, 16, JSON_THROW_ON_ERROR), 'updated_at' => (int)$raw['updated_at']];
}

if (defined('ITHAKYA_PILOT_LIBRARY')) return;

/* ---------- Traitement d'une requête HTTP ---------- */

header_remove('X-Powered-By');   /* R7-UX360 31/10/2026 : ne pas divulguer la version de PHP. */
/* TECH-07 : identifiant de corrélation (8 hexadécimaux aléatoires, sans lien avec une personne) renvoyé en en-tête et repris au journal serveur. */
$itpRequestId = bin2hex(random_bytes(4));
$itpCreditEvent = null;
header('X-Request-Id: ' . $itpRequestId);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, private, max-age=0');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header('X-Content-Type-Options: nosniff');
header("Content-Security-Policy: default-src 'none'; frame-ancestors 'none'");
header('Referrer-Policy: no-referrer');

try {
    if (PHP_VERSION_ID < 80200) fail(503, 'runtime', 'Le pilote privé attend un environnement compatible.');
    $config = loadConfig(getenv('ITHAKYA_PILOT_CONFIG') ?: dirname(__DIR__, 2) . '/ithakya-pilote-prive/config.php', dirname(__DIR__));
    if (($config['enabled'] ?? false) !== true) {
        fail(503, 'not_configured', 'Les comptes ne sont pas encore disponibles sur cette installation privée. La découverte reste accessible.');
    }
    $origin = $config['origin'] ?? '';
    $parts = is_string($origin) ? parse_url($origin) : false;
    if (!$parts || isset($parts['path']) || isset($parts['query']) || isset($parts['fragment']) || isset($parts['user']) || isset($parts['pass']) || !isset($parts['scheme'], $parts['host'])) {
        fail(503, 'configuration', 'Le pilote privé attend sa configuration.');
    }
    $host = $parts['host'] . (isset($parts['port']) ? ':' . $parts['port'] : '');
    if (($_SERVER['HTTP_HOST'] ?? '') !== $host) fail(403, 'host', 'Cet accès n’est pas autorisé pour le pilote.');
    $local = $config['environment'] === 'local';
    if ($local) {
        if (!in_array($_SERVER['REMOTE_ADDR'] ?? '', ['127.0.0.1', '::1'], true)
            || !in_array($parts['host'], ['127.0.0.1', 'localhost', '::1'], true)) {
            fail(403, 'local_only', 'Cet environnement de test reste local.');
        }
    } elseif ($parts['scheme'] !== 'https' || (($_SERVER['HTTPS'] ?? '') !== 'on' && (int)($_SERVER['SERVER_PORT'] ?? 0) !== 443)) {
        fail(426, 'https_required', 'Une connexion HTTPS est requise pour le pilote.');
    }
    startPilotSession($config, $local);
    $db = openDatabase($config);
    ensureSchema($db, $config);
    $user = loggedUser($db);
    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    $action = $_GET['action'] ?? 'session';
    if (!is_string($action) || !preg_match('/^[a-z_]+$/D', $action)) fail(404, 'action', 'Cette action n’existe pas.');
    if ($action === 'lecture_media') {
        if (!in_array($method, ['GET', 'HEAD'], true)) fail(405, 'method', 'Méthode non autorisée.');
        itpPilotRequestGuard($db, $config, $user, $action, $method);
        itpProofServe($db, $config, authenticated($user), $method);
    }
    $input = [];
    if ($method === 'POST') {
        if (($_SERVER['HTTP_ORIGIN'] ?? '') !== $origin) fail(403, 'origin', 'L’origine de cette demande n’est pas autorisée.');
        if (inputMediaType($_SERVER['CONTENT_TYPE'] ?? '') !== 'application/json') fail(415, 'content_type', 'Le format de cette demande n’est pas accepté.');
        if (!hash_equals($_SESSION['csrf'], $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) fail(403, 'csrf', 'La session a changé. Reconnectez-vous pour continuer ; votre texte reste dans le formulaire.');
        if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 16384) fail(413, 'too_large', 'La demande est trop volumineuse.');
        $body = file_get_contents('php://input', false, null, 0, 16385);
        if ($body === false || strlen($body) > 16384) fail(413, 'too_large', 'La demande est trop volumineuse.');
        try { $input = json_decode($body, true, 16, JSON_THROW_ON_ERROR); }
        catch (JsonException) { fail(400, 'json', 'La demande n’est pas lisible.'); }
        if (!is_array($input) || (array_is_list($input) && $input !== [])) fail(400, 'json', 'La demande n’est pas lisible.');
    } elseif ($method !== 'GET') {
        header('Allow: GET, POST');
        fail(405, 'method', 'Cette méthode n’est pas autorisée.');
    }
    if ($action === 'progress' && $method === 'POST'
        && in_array($input['event'] ?? null, ITP_CREDIT_EVENTS, true)) {
        $itpCreditEvent = $input['event'];
    }
    $readActions = ['waitlist_info', 'waitlist_admin', 'lecture_reviews', 'session', 'profile', 'feed', 'state', 'progression', 'oeuvres', 'moderation', 'gift_offers', 'gift_claims', 'gift_admin', 'attenzia_agregats', 'attenzia_instantanes', 'attenzia_instantane', 'attenzia_comparer', 'attenzia_export', 'attenzia_journal', 'avatars', 'avatar_image', 'avatars_admin'];
    $writeActions = ['waitlist_join', 'waitlist_withdraw', 'gift_preview', 'lecture_decide', 'register', 'login', 'logout', 'profile', 'invite', 'post', 'remove', 'progress', 'password', 'seen',
        'recover', 'recovery_code', 'reset_link', 'logout_others', 'state', 'report', 'moderate', 'delete_account', 'gift_claim', 'gift_decide', 'gift_draft', 'gift_publish', 'avatar_revue', 'avatar_statut', 'react', 'attenzia_instantane_creer', 'attenzia_purger', 'lecture_suivi'];
    if (($method === 'GET' && !in_array($action, $readActions, true)) || ($method === 'POST' && !in_array($action, $writeActions, true))) {
        fail(405, 'method', 'Cette action n’est pas autorisée avec cette méthode.');
    }
    itpPilotRequestGuard($db, $config, $user, $action, $method);
    itpWaitlistHandle($db, $config, $user, $action, $input);
    if ($action === 'lecture_suivi') itpProofClock($db, $config, authenticated($user), $input);
    itpCreditHandle($db, $config, $user, $action, $input);
    /* Une session anonyme n'affiche aucun avatar. Le registre M09 peut encore être absent sur une base neuve. */
    if ($action !== 'session' || $user !== null) itpAvatarCatalogue($db);
    itpEcoHandle($db, $config, $user, $action, $input);
    if (in_array($action, ['gift_preview', 'gift_offers', 'gift_claims', 'gift_claim', 'gift_decide', 'gift_admin', 'gift_draft', 'gift_publish'], true)) itpGiftHandle($db, $config, $user, $action, $method, $input);
    itpAtzHandle($db, $config, $user, $action, $method, $input, $local);   /* V1 final : ATTENZIA instantanés figés (retourne sans effet pour toute autre action) */
    if ($action === 'session') output(['ok' => true, 'csrf' => $_SESSION['csrf'], 'user' => $user ? publicUser($user) : null]);
    if ($action === 'avatars') {
        /* M09 — catalogue public (aucune donnée personnelle) : identifiants OUVERTS, image versionnée, portrait seulement s'il est activé. */
        $cat = itpAvatarCatalogue($db); $source = 'base';
        if ($cat === null) {
            $source = 'repli_m08'; $cat = [];
            $ids = ITP_AVATARS_CLASSIQUES;
            for ($f = 1; $f <= 6; $f++) for ($n = 1; $n <= 10; $n++) $ids[] = sprintf('av0%d%02d', $f, $n);
            for ($n = 1; $n <= 90; $n++) $ids[] = sprintf('av10%02d', $n);
            foreach ($ids as $i) $cat[$i] = ['id' => $i, 'nom' => $i, 'famille' => null, 'classique' => !str_starts_with($i, 'av'), 'ouvert' => true, 'portrait_valide' => false, 'image' => 'assets/avatars/' . $i . '.svg', 'tailles' => (object)[]];
        }
        $cat += itpAvatarVariantesP1() + itpAvatarPortraitsP2();
        $liste = array_values(array_map(fn($a) => array_diff_key($a, ['ouvert' => 1]), array_filter($cat, fn($a) => $a['ouvert'])));
        $par = (int)($_GET['par'] ?? 200); $page = (int)($_GET['page'] ?? 1);
        if ($par < 1 || $par > 200 || $page < 1) fail(422, 'pagination', 'Pagination invalide (par : 1 à 200 ; page ≥ 1).');
        $corps = ['ok' => true, 'source' => $source, 'total' => count($liste), 'page' => $page, 'par' => $par, 'pages' => (int)ceil(count($liste) / $par), 'avatars' => array_slice($liste, ($page - 1) * $par, $par)];
        $etag = '"' . substr(hash('sha256', json_encode($corps, JSON_THROW_ON_ERROR)), 0, 32) . '"';
        header('Cache-Control: public, max-age=60'); header('ETag: ' . $etag);
        if (trim($_SERVER['HTTP_IF_NONE_MATCH'] ?? '') === $etag) { http_response_code(304); exit; }
        output($corps);
    }
    if ($action === 'avatar_image') {
        /* Portrait d'un avatar : servi depuis le stockage privé UNIQUEMENT s'il est activé ; 404 sinon (révocation immédiate). */
        $id = $_GET['id'] ?? ''; $t = (int)($_GET['t'] ?? 0);
        if (!is_string($id) || !preg_match(ITP_AVATAR_MOTIF, $id) || !in_array($t, ITP_AVATAR_TAILLES, true)) fail(404, 'avatar', 'Portrait inconnu.');
        try { $a = dbQuery($db, "SELECT s.path, s.bytes, s.sha256, s.stockage FROM itp_avatars a JOIN itp_avatar_assets s ON s.avatar_id = a.id AND s.role = ? WHERE a.id = ? AND a.portrait_statut = 'enabled' ORDER BY s.id DESC LIMIT 1", ['portrait_' . $t, $id])->fetch(); }
        catch (PDOException) { $a = false; }
        if (!$a || $a['stockage'] !== 'prive' || !preg_match('~^avatars/derives/av[0-9]{4}/portrait_(64|128|256|512)\.webp$~D', $a['path'])) fail(404, 'avatar', 'Portrait non publié.');
        $f = $config['_private'] . '/' . $a['path'];
        if (!is_file($f) || is_link($f) || filesize($f) !== (int)$a['bytes']) fail(404, 'avatar', 'Portrait indisponible.');
        $etag = '"' . substr($a['sha256'], 0, 24) . '"';
        header('Content-Type: image/webp'); header('X-Content-Type-Options: nosniff'); header('ETag: ' . $etag);
        header('Cache-Control: public, max-age=86400');
        if (trim($_SERVER['HTTP_IF_NONE_MATCH'] ?? '') === $etag) { http_response_code(304); exit; }
        header('Content-Length: ' . (int)$a['bytes']); readfile($f); exit;
    }
    if (in_array($action, ['avatars_admin', 'avatar_revue', 'avatar_statut'], true)) {
        $u = authenticated($user); $rolesAv = itpAvatarRolesP2($db, $u);
        if (!array_intersect($rolesAv, ['admin', 'editeur', 'juriste'])) fail(403, 'role_requis', 'Action réservée aux comptes éditoriaux ou juridiques.');
        if (itpAvatarCatalogue($db) === null) fail(503, 'avatars_migration', 'Le registre des avatars attend sa migration privée.');
        if ($action === 'avatars_admin') {
            $rows = dbQuery($db, 'SELECT a.id, a.nom, a.famille, a.portrait_statut, a.version, a.droits, a.validated_at, (SELECT COUNT(*) FROM itp_avatar_reviews r WHERE r.avatar_id = a.id) AS revues FROM itp_avatars a ORDER BY a.classique DESC, a.id')->fetchAll();
            output(['ok' => true, 'avatars' => $rows]);
        }
        $id = $input['avatar_id'] ?? ''; $version = $input['version'] ?? null;
        if (!is_string($id) || !preg_match(ITP_AVATAR_MOTIF, $id) || !is_int($version)) fail(422, 'avatar', 'Identifiant ou version invalide.');
        $db->beginTransaction();
        try {
            $av = dbQuery($db, 'SELECT * FROM itp_avatars WHERE id = ?' . (driver($db) === 'mysql' ? ' FOR UPDATE' : ''), [$id])->fetch();
            if (!$av) fail(404, 'avatar', 'Avatar inconnu.');
            if ((int)$av['version'] !== $version) fail(409, 'version', 'Version périmée : rechargez la fiche.');
            if ($action === 'avatar_revue') {
                fields($input, ['avatar_id', 'version', 'scores', 'decision', 'justification']);
                if (!array_intersect($rolesAv, ['admin', 'editeur'])) fail(403, 'role_requis', 'La revue artistique est réservée à l’éditeur.');
                if (!in_array($av['portrait_statut'], ['produced_unreviewed', 'needs_revision'], true)) fail(409, 'statut', 'Aucun portrait produit en attente de revue pour cet avatar.');
                $b = ['presence' => 20, 'singularite' => 15, 'adequation' => 20, 'lisibilite' => 15, 'lumiere' => 15, 'coherence' => 15]; $sc = $input['scores'] ?? null;
                if (!is_array($sc) || array_diff_key($b, $sc) || array_diff_key($sc, $b)) fail(422, 'scores', 'Les six critères sont requis.');
                foreach ($b as $k => $max) if (!is_int($sc[$k] ?? null) || $sc[$k] < 0 || $sc[$k] > $max) fail(422, 'scores', 'Note hors bornes : ' . $k);
                $total = array_sum(array_map(fn($k) => $sc[$k], array_keys($b))); $dec = $input['decision'] ?? '';
                if (!in_array($dec, ['art_approved', 'needs_revision', 'rejected'], true)) fail(422, 'decision', 'Décision inconnue.');
                if ($dec === 'art_approved' && $total < 85) fail(422, 'seuil', 'Approbation artistique impossible sous 85/100 (' . $total . ').');
                $just = text($input['justification'] ?? '', 20, 1000);
                dbQuery($db, 'INSERT INTO itp_avatar_reviews (avatar_id, version, relecteur, created_at, s_presence, s_singularite, s_adequation, s_lisibilite, s_lumiere, s_coherence, total, decision, justification) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    [$id, $version, $u['id'], time(), $sc['presence'], $sc['singularite'], $sc['adequation'], $sc['lisibilite'], $sc['lumiere'], $sc['coherence'], $total, $dec, $just]);
                dbQuery($db, 'UPDATE itp_avatars SET portrait_statut = ?, version = version + 1, updated_at = ? WHERE id = ?', [$dec, time(), $id]);
                itpAvatarVersion($db, $id, $u['id'], 'revue ' . $dec . ' ' . $total . '/100');
            } else {
                fields($input, ['avatar_id', 'version', 'cible', 'droits', 'motif']);
                $cible = $input['cible'] ?? ''; $motif = text($input['motif'] ?? '', 5, 160);
                if ($cible === 'tech_approved') {
                    if ($av['portrait_statut'] !== 'art_approved') fail(409, 'statut', 'Le contrôle technique suit l’approbation artistique.');
                    $pb = itpAvatarControleTechnique($db, $config, $id); if ($pb) fail(409, 'controle_technique', 'Contrôle technique non conforme : ' . implode(' ; ', $pb));
                    dbQuery($db, 'UPDATE itp_avatars SET portrait_statut = ?, version = version + 1, updated_at = ? WHERE id = ?', ['tech_approved', time(), $id]);
                } elseif ($cible === 'enabled') {
                    if (!array_intersect($rolesAv, ['admin', 'juriste'])) fail(403, 'role_requis', 'L’activation est réservée au juriste.');
                    if ($av['portrait_statut'] !== 'tech_approved') fail(409, 'statut', 'Activation impossible : contrôle technique requis.');
                    $rev = dbQuery($db, "SELECT relecteur, total FROM itp_avatar_reviews WHERE avatar_id = ? AND decision = 'art_approved' ORDER BY id DESC LIMIT 1", [$id])->fetch();
                    if (!$rev || (int)$rev['total'] < 85) fail(409, 'revue', 'Activation impossible sans revue artistique ≥ 85/100.');
                    if ($rev['relecteur'] === $u['id']) fail(409, 'quatre_yeux', 'L’activation doit être faite par un autre compte que le relecteur artistique.');
                    $pb = itpAvatarControleTechnique($db, $config, $id); if ($pb) fail(409, 'controle_technique', 'Contrôle technique non conforme : ' . implode(' ; ', $pb));
                    $droits = text($input['droits'] ?? '', 8, 255);
                    dbQuery($db, 'UPDATE itp_avatars SET portrait_statut = ?, droits = ?, validated_by = ?, validated_at = ?, version = version + 1, updated_at = ? WHERE id = ?', ['enabled', $droits, $u['id'], time(), time(), $id]);
                } elseif ($cible === 'disabled') {
                    if ($av['portrait_statut'] !== 'enabled') fail(409, 'statut', 'Ce portrait n’est pas activé.');
                    dbQuery($db, 'UPDATE itp_avatars SET portrait_statut = ?, version = version + 1, updated_at = ? WHERE id = ?', ['tech_approved', time(), $id]);
                } else fail(422, 'cible', 'Transition inconnue.');
                itpAvatarVersion($db, $id, $u['id'], $cible . ' : ' . $motif);
            }
            $db->commit();
        } catch (Throwable $e) { if ($db->inTransaction()) $db->rollBack(); throw $e; }
        output(['ok' => true, 'avatar' => dbQuery($db, 'SELECT id, portrait_statut, version, droits, validated_by, validated_at FROM itp_avatars WHERE id = ?', [$id])->fetch()]);
    }
    if ($action === 'oeuvres' && !$user) {
        /* Programmation publique du registre (sans compte) : œuvres accessibles aux visiteurs, aucune donnée personnelle. */
        $list = [];
        foreach (itpWorks($config) as $w) if (in_array($w['universe'], ITP_MEMBER_CONTEXTS, true) && $w['statut'] !== 'retiree')
            $list[] = ['oeuvre' => $w['id'], 'univers' => $w['universe'], 'historique' => $w['legacy'], 'statut' => $w['statut'], 'titre' => $w['titre'], 'territoires' => $w['territoires'], 'idees' => $w['idees'], 'court' => $w['court'], 'long' => $w['long']];
        output(['ok' => true, 'connected' => false, 'territoires' => array_keys(ITP_TERRITOIRES), 'oeuvres' => $list]);
    }

    if ($action === 'register') {
        fields($input, ['login', 'display_name', 'password', 'invitation', 'avatar', 'interests']);
        if ($user) fail(409, 'already_logged_in', 'Déconnectez-vous avant de créer un autre compte.');
        $login = strtolower(trim(is_string($input['login'] ?? null) ? $input['login'] : ''));
        if (!preg_match('/^[a-z0-9][a-z0-9_-]{2,31}$/D', $login)) fail(422, 'login', 'L’identifiant doit contenir 3 à 32 lettres non accentuées, chiffres, tirets ou soulignés.');
        [$name, $avatar, $interests] = cleanProfile($input, $db);
        $password = checkedPassword($input['password'] ?? null);
        if (array_key_exists('invitation', $input) && !is_string($input['invitation'])) fail(422, 'invitation', 'Lien d’habilitation invalide.');
        $invitation = is_string($input['invitation'] ?? null) ? trim($input['invitation']) : '';
        $tokenHash = hash('sha256', $invitation);
        $invite = strlen($invitation) >= 32 && strlen($invitation) <= 128
            ? dbQuery($db, 'SELECT role FROM itp_invites WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?', [$tokenHash, time()])->fetch()
            : false;
        $role = 'member';
        if ($invitation === '') {
            // Protections temporaires contre l'abus, indépendantes du nombre de comptes.
            throttle($db, 'register_public', $_SERVER['REMOTE_ADDR'] ?? '', 30, 60, $config);
        } else {
            if (!$invite || !in_array($invite['role'], ['member', 'partner', 'admin'], true)) {
                throttle($db, 'register_invalid', $_SERVER['REMOTE_ADDR'] ?? '', 10, 900, $config);
                fail(403, 'invitation', 'Ce lien d’habilitation est invalide ou a déjà été utilisé.');
            }
            throttle($db, 'register_invite', $tokenHash, 6, 900, $config);
            $role = $invite['role'];
        }
        $hash = hashPassword($password, $config);
        $id = bin2hex(random_bytes(16));
        $db->beginTransaction();
        try {
            if ($invitation !== '') {
                $taken = dbQuery($db, 'UPDATE itp_invites SET used_at = ?, used_by = ? WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?', [time(), $id, $tokenHash, time()]);
                if ($taken->rowCount() !== 1) fail(403, 'invitation', 'Ce lien d’habilitation a expiré ou a déjà été utilisé.');
            }
            dbQuery($db, 'INSERT INTO itp_users (id, login, display_name, password_hash, avatar, interests, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [$id, $login, $name, $hash, $avatar, $interests, $role, time()]);
            if ($invitation !== '') itpWaitlistAdmissionCleanup($db, $tokenHash);
            $db->commit();
        } catch (Throwable $e) {
            if ($db->inTransaction()) $db->rollBack();
            if ($e instanceof PDOException && in_array((string)$e->getCode(), ['23000', '23505'], true)) fail(409, 'login_taken', 'Cet identifiant est déjà utilisé. Choisissez-en un autre.');
            throw $e;
        }
        resetSession();
        $_SESSION['user_id'] = $id; $_SESSION['auth_version'] = 1;
        /* Code personnel de récupération, montré une seule fois. Son échec n'annule pas le compte créé : le code pourra être émis depuis le profil. */
        $code = null;
        try { $code = issueRecoveryCode($db, $id, $config); } catch (Throwable) { error_log('ITHAKYA pilot: recovery code not issued at registration.'); }
        output(['ok' => true, 'csrf' => $_SESSION['csrf'], 'user' => publicUser(loggedUser($db)), 'recovery_code' => $code], 201);
    }
    if ($action === 'login') {
        fields($input, ['login', 'password']);
        throttle($db, 'login_ip', $_SERVER['REMOTE_ADDR'] ?? '', 20, 900, $config);
        $login = strtolower(trim(is_string($input['login'] ?? null) ? $input['login'] : ''));
        throttle($db, 'login_name', substr($login, 0, 40), 10, 900, $config);
        $password = is_string($input['password'] ?? null) && strlen($input['password']) <= 1024 ? $input['password'] : '';
        $record = dbQuery($db, 'SELECT * FROM itp_users WHERE login = ?', [$login])->fetch();
        $dummyBcrypt = '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi';
        $dummyArgon = '$argon2id$v=19$m=19456,t=2,p=1$RlRaWnR0RTA2ajFzak9OQg$PCRtlddqq9cfdAxCGA2R1vlO05lIzsSrrHcN8NlQDqU';
        $material = passwordMaterial($password, $config);
        $stored = $record['password_hash'] ?? null;
        $valid = $stored !== null && password_verify($material, $stored);
        if (!$valid) {
            // On failure, verify both supported policies once. Successful logins keep their original hashing budget.
            $algorithm = $stored === null ? '' : password_get_info($stored)['algoName'];
            if ($algorithm !== 'bcrypt') password_verify($material, $dummyBcrypt);
            if (defined('PASSWORD_ARGON2ID') && $algorithm !== 'argon2id') password_verify($material, $dummyArgon);
            fail(401, 'credentials', 'Identifiant ou phrase de passe incorrect.');
        }
        resetSession();
        $_SESSION['user_id'] = $record['id']; $_SESSION['auth_version'] = (int)$record['auth_version'];
        output(['ok' => true, 'csrf' => $_SESSION['csrf'], 'user' => publicUser($record)]);
    }
    if ($action === 'recover') {
        /* Récupération sans session : code personnel (login + code) ou lien émis par l'administrateur (jeton seul). */
        fields($input, ['login', 'code', 'token', 'new_password']);
        throttle($db, 'recover_ip', $_SERVER['REMOTE_ADDR'] ?? '', 10, 900, $config);
        $newPassword = checkedPassword($input['new_password'] ?? null);
        $code = is_string($input['code'] ?? null) ? $input['code'] : ''; $token = is_string($input['token'] ?? null) ? $input['token'] : '';
        if (($code === '') === ($token === '')) fail(422, 'recovery', 'Indiquez votre code de récupération ou utilisez le lien reçu.');
        if ($code !== '') {
            $login = strtolower(trim(is_string($input['login'] ?? null) ? $input['login'] : ''));
            throttle($db, 'recover_name', substr($login, 0, 40), 5, 900, $config);
            if (strlen(normalizedCode($code)) !== 24) fail(401, 'recovery_invalid', 'Identifiant ou code de récupération incorrect, ou code déjà utilisé.');
            $row = dbQuery($db, "SELECT r.token_hash, r.user_id, r.expires_at, r.used_at FROM itp_recovery r JOIN itp_users u ON u.id = r.user_id WHERE r.token_hash = ? AND r.kind = 'code' AND u.login = ?", [recoveryHash('code', $code, $config), $login])->fetch();
            if (!$row || $row['used_at'] !== null || (int)$row['expires_at'] <= time()) fail(401, 'recovery_invalid', 'Identifiant ou code de récupération incorrect, ou code déjà utilisé.');
        } else {
            if (!preg_match('/^[a-f0-9]{48}$/D', $token)) fail(401, 'recovery_invalid', 'Ce lien de réinitialisation n’est pas valide.');
            $row = dbQuery($db, "SELECT token_hash, user_id, expires_at, used_at FROM itp_recovery WHERE token_hash = ? AND kind = 'link'", [recoveryHash('link', $token, $config)])->fetch();
            if (!$row || $row['used_at'] !== null) fail(401, 'recovery_invalid', 'Ce lien de réinitialisation n’est pas valide ou a déjà servi.');
            if ((int)$row['expires_at'] <= time()) fail(410, 'recovery_expired', 'Ce lien de réinitialisation a expiré. Demandez-en un nouveau à l’administrateur du pilote.');
        }
        $hash = hashPassword($newPassword, $config);
        $db->beginTransaction();
        $taken = dbQuery($db, 'UPDATE itp_recovery SET used_at = ? WHERE token_hash = ? AND used_at IS NULL', [time(), $row['token_hash']]);
        if ($taken->rowCount() !== 1) fail(401, 'recovery_invalid', 'Ce code ou ce lien a déjà servi.');
        dbQuery($db, 'UPDATE itp_users SET password_hash = ?, auth_version = auth_version + 1 WHERE id = ?', [$hash, $row['user_id']]);
        /* Les liens encore ouverts pour ce compte sont fermés : un seul changement par récupération. */
        dbQuery($db, "UPDATE itp_recovery SET used_at = ? WHERE user_id = ? AND kind = 'link' AND used_at IS NULL", [time(), $row['user_id']]);
        $db->commit();
        $record = dbQuery($db, 'SELECT * FROM itp_users WHERE id = ?', [$row['user_id']])->fetch();
        $fresh = null;
        try { $fresh = issueRecoveryCode($db, $record['id'], $config); } catch (Throwable) { error_log('ITHAKYA pilot: recovery code not renewed.'); }
        resetSession();
        $_SESSION['user_id'] = $record['id']; $_SESSION['auth_version'] = (int)$record['auth_version'];
        output(['ok' => true, 'csrf' => $_SESSION['csrf'], 'user' => publicUser($record), 'recovery_code' => $fresh]);
    }
    $user = authenticated($user);
    if ($action === 'recovery_code') {
        fields($input, ['current_password']);
        throttle($db, 'password', $user['id'], 6, 900, $config);
        if (!is_string($input['current_password'] ?? null) || strlen($input['current_password']) > 1024 || !password_verify(passwordMaterial($input['current_password'], $config), $user['password_hash'])) {
            fail(401, 'credentials', 'La phrase de passe actuelle est incorrecte.');
        }
        output(['ok' => true, 'recovery_code' => issueRecoveryCode($db, $user['id'], $config)], 201);
    }
    if ($action === 'reset_link') {
        fields($input, ['login']);
        if ($user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administrateur du pilote.');
        throttle($db, 'reset_link', $user['id'], 20, 3600, $config);
        $login = strtolower(trim(is_string($input['login'] ?? null) ? $input['login'] : ''));
        $target = dbQuery($db, 'SELECT id FROM itp_users WHERE login = ?', [$login])->fetchColumn();
        if (!$target) fail(404, 'unknown_login', 'Aucun compte ne porte cet identifiant.');
        $token = bin2hex(random_bytes(24));
        dbQuery($db, 'INSERT INTO itp_recovery (token_hash, user_id, kind, created_at, expires_at) VALUES (?, ?, ?, ?, ?)', [recoveryHash('link', $token, $config), $target, 'link', time(), time() + ITP_RESET_TTL]);
        output(['ok' => true, 'token' => $token, 'expires_at' => time() + ITP_RESET_TTL], 201);
    }
    if ($action === 'logout_others') {
        fields($input, []);
        dbQuery($db, 'UPDATE itp_users SET auth_version = auth_version + 1 WHERE id = ?', [$user['id']]);
        resetSession(); $_SESSION['user_id'] = $user['id']; $_SESSION['auth_version'] = (int)$user['auth_version'] + 1;
        output(['ok' => true, 'csrf' => $_SESSION['csrf']]);
    }
    $modeAttenzia = 'attenzia_mode';
    if ($action === 'state' && ($method === 'GET' ? ($_GET['key'] ?? null) : ($input['key'] ?? null)) === $modeAttenzia) {
        if ($method === 'GET') {
            $state = readState($db, $user['id'], $modeAttenzia);
            output(['ok' => true, 'key' => $modeAttenzia, 'data' => ['actif' => ($state['data']['actif'] ?? false) === true]]);
        }
        fields($input, ['key', 'actif', 'owner_id']);
        assertContributionOwner($input['owner_id'] ?? null, $user);
        if (!is_bool($input['actif'] ?? null)) fail(422, 'attenzia_mode', 'Choisissez un mode de découverte.');
        throttle($db, $modeAttenzia, $user['id'], 30, 60, $config);
        if ($input['actif']) {
            $sql = 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?)';
            $sql .= driver($db) === 'mysql'
                ? ' ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = VALUES(updated_at)'
                : ' ON CONFLICT(user_id, state_key) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at';
            dbQuery($db, $sql, [$user['id'], $modeAttenzia, '{"actif":true}', time()]);
        } else {
            dbQuery($db, 'DELETE FROM itp_states WHERE user_id = ? AND state_key = ?', [$user['id'], $modeAttenzia]);
        }
        output(['ok' => true, 'key' => $modeAttenzia, 'data' => ['actif' => $input['actif']]]);
    }
    if ($action === 'state' && $method === 'GET') {
        $key = $_GET['key'] ?? '';
        if (!in_array($key, ['traversee', 'gardes', 'lecture', 'mission'], true)) fail(404, 'state', 'Cet état n’existe pas.');
        $state = readState($db, $user['id'], $key);
        if (!in_array($key, ['traversee'], true) && $state['updated_at'] === null) $state['data'] = (object)[];
        output(['ok' => true, 'key' => $key, 'data' => $state['data'], 'updated_at' => $state['updated_at']]);
    }
    if ($action === 'state' && in_array($input['key'] ?? '', ['gardes', 'lecture'], true)) {
        /* gardes : découvertes gardées du catalogue (ajout idempotent, retrait sans effacer l'historique de lecture).
         * lecture : position par contenu ; en cas de conflit entre appareils, la mesure la plus récente (at) l'emporte. */
        fields($input, ['key', 'add', 'remove', 'content', 'position', 'duration', 'at', 'reset', 'owner_id', 'vu']);
        /* R16.2 : le compte initiateur est obligatoire, y compris pour les anciens favoris.
         * Un envoi différé après changement de session ne modifie pas le compte suivant. */
        assertContributionOwner($input['owner_id'] ?? null, $user);
        /* Effacement de l'historique de lecture ou de la liste gardée (RF-29) : portée exacte, autres données intactes. */
        /* R16.2 : owner_id est maintenant obligatoire ; le reset explicite a TROIS champs. */
        if (isStateResetOnly($input)) {
            dbQuery($db, 'DELETE FROM itp_states WHERE user_id = ? AND state_key = ?', [$user['id'], $input['key']]);
            output(['ok' => true, 'key' => $input['key'], 'data' => (object)[], 'updated_at' => null]);
        }
        $key = $input['key'];
        throttle($db, 'state', $user['id'], 60, 60, $config);
        $db->beginTransaction();
        if (driver($db) === 'mysql') dbQuery($db, 'SELECT id FROM itp_users WHERE id = ? FOR UPDATE', [$user['id']])->fetch();
        else dbQuery($db, 'UPDATE itp_users SET auth_version = auth_version WHERE id = ?', [$user['id']]);
        $current = readState($db, $user['id'], $key); $data = $current['updated_at'] === null ? [] : (array)$current['data'];
        /* M2 : en plus des identifiants historiques, Court et Long de toute œuvre accessible du registre (« <œuvre>.court|long »). */
        $id = function ($v) use ($config, $user) {
            if (is_string($v) && preg_match('/^(signature|pop|progression|soleil|traversee)\.[a-z0-9-]+(\.[0-9]+)?$/D', $v)) return $v;
            $found = is_string($v) && strlen($v) <= 80 ? itpWorkContent($config, $v) : null;
            if ($found && in_array($found[0]['universe'], allowedContexts($user), true)) return $v;
            fail(422, 'content', 'Ce contenu n’est pas reconnu.');
        };
        if ($key === 'gardes') {
            if (($input['reset'] ?? false) === true) $data = [];
            if (isset($input['add'])) { $c = $id($input['add']); if (!isset($data[$c])) $data[$c] = time(); }
            if (isset($input['remove'])) unset($data[$id($input['remove'])]);
            if (count($data) > 200) fail(422, 'too_many', 'La liste des découvertes gardées est complète (200).');
        } else {
            $c = $id($input['content'] ?? null); $pos = $input['position'] ?? null; $dur = $input['duration'] ?? null; $at = $input['at'] ?? null;
            $lecture = normaliserLecture($pos, $dur, $at);
            /* Corrige aussi un ancien marqueur enregistré avec une horloge
             * future (ancienne API acceptait jusqu'à +24 h). */
            $nowMs = (int)round(microtime(true) * 1000);
            $avant = isset($data[$c]) && is_array($data[$c]) ? $data[$c] : null;
            /* L20 : intervalles vus cumulés entre sessions et appareils (une reprise à la dernière position ne doit pas
             * faire perdre ce qui a déjà été regardé). Fusionnés quel que soit l'horodatage ; remis à zéro si la durée change. */
            $vuAvant = ($avant && abs((float)($avant['duration'] ?? 0) - $lecture['duration']) <= 1) ? ($avant['vu'] ?? []) : [];
            $vu = fusionnerVu($vuAvant, array_key_exists('vu', $input) ? normaliserVu($input['vu'], $lecture['duration']) : []);
            if (remplacerLecture($avant, $lecture, $nowMs)) $data[$c] = $lecture; elseif (!$avant) $data[$c] = $lecture;
            if ($vu) $data[$c]['vu'] = $vu; else unset($data[$c]['vu']);
            if (count($data) > 100) { uasort($data, fn($a, $b) => $b['at'] <=> $a['at']); $data = array_slice($data, 0, 100, true); }
        }
        $json = json_encode($data ?: (object)[], JSON_THROW_ON_ERROR);
        if (driver($db) === 'mysql') dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = VALUES(updated_at)', [$user['id'], $key, $json, time()]);
        else dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, state_key) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at', [$user['id'], $key, $json, time()]);
        $db->commit();
        output(['ok' => true, 'key' => $key, 'data' => $data ?: (object)[], 'updated_at' => time()]);
    }
    if ($action === 'state' && ($input['key'] ?? '') === 'mission') {
        /* V1 : état d'une mission narrative. Monotone (un parcours ne recule pas), borné, sans effet sur les Points. */
        fields($input, ['key', 'mission', 'choix', 'termine', 'regard', 'owner_id']);
        assertContributionOwner($input['owner_id'] ?? null, $user);
        $mid = $input['mission'] ?? null;
        if (!is_string($mid) || !array_key_exists($mid, ITP_MISSIONS)) fail(422, 'mission', 'Cette mission n’existe pas.');
        $choix = $input['choix'] ?? null;
        if (!is_array($choix) || !array_is_list($choix) || count($choix) > 12) fail(422, 'mission', 'Ce parcours de mission n’est pas reconnu.');
        foreach ($choix as $c) if (!is_int($c) || $c < 0 || $c > 9) fail(422, 'mission', 'Ce choix de mission n’est pas reconnu.');
        $termine = $input['termine'] ?? null; $regard = $input['regard'] ?? null;
        if (!is_bool($termine)) fail(422, 'mission', 'La demande est incomplète.');
        if ($regard !== null && (!is_string($regard) || !in_array($regard, ITP_MISSIONS[$mid], true))) fail(422, 'mission', 'Ce regard n’est pas reconnu.');
        throttle($db, 'state', $user['id'], 60, 60, $config);
        $db->beginTransaction();
        if (driver($db) === 'mysql') dbQuery($db, 'SELECT id FROM itp_users WHERE id = ? FOR UPDATE', [$user['id']])->fetch();
        else dbQuery($db, 'UPDATE itp_users SET auth_version = auth_version WHERE id = ?', [$user['id']]);
        $current = readState($db, $user['id'], 'mission'); $data = $current['updated_at'] === null ? [] : (array)$current['data'];
        $avant = isset($data[$mid]) && is_array($data[$mid]) ? $data[$mid] : null;
        if (!$avant || count($choix) >= count($avant['choix'] ?? []) || ($termine && empty($avant['termine']))) {
            if ($avant && !empty($avant['termine'])) { $termine = true; $regard = $avant['regard'] ?? $regard; $choix = $avant['choix']; }
            $data[$mid] = ['choix' => $choix, 'termine' => $termine, 'regard' => $regard, 'at' => time()];
        }
        $json = json_encode($data, JSON_THROW_ON_ERROR);
        if (driver($db) === 'mysql') dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = VALUES(updated_at)', [$user['id'], 'mission', $json, time()]);
        else dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, state_key) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at', [$user['id'], 'mission', $json, time()]);
        $db->commit();
        output(['ok' => true, 'key' => 'mission', 'data' => $data, 'updated_at' => time()]);
    }
    if ($action === 'state') {
        fields($input, ['key', 'data', 'reset', 'owner_id']);
        if (($input['key'] ?? '') !== 'traversee') fail(404, 'state', 'Cet état n’existe pas.');
        /* R16.2 : toutes les écritures Traversée doivent être liées au compte initiateur. */
        assertContributionOwner($input['owner_id'] ?? null, $user);
        throttle($db, 'state', $user['id'], 60, 60, $config);
        if (($input['reset'] ?? false) === true) {
            dbQuery($db, 'DELETE FROM itp_states WHERE user_id = ? AND state_key = ?', [$user['id'], 'traversee']);
            output(['ok' => true, 'key' => 'traversee', 'data' => emptyTraversee(), 'updated_at' => null]);
        }
        /* Fusion : une étape validée reste validée ; un choix peut être changé. */
        $incoming = cleanTraversee($input['data'] ?? null);
        $db->beginTransaction();
        if (driver($db) === 'mysql') dbQuery($db, 'SELECT id FROM itp_users WHERE id = ? FOR UPDATE', [$user['id']])->fetch();
        else dbQuery($db, 'UPDATE itp_users SET auth_version = auth_version WHERE id = ?', [$user['id']]);
        $current = readState($db, $user['id'], 'traversee')['data'];
        $chapters = (array)($current['chapters'] ?? []); $choices = (array)($current['choices'] ?? []);
        foreach ((array)$incoming['chapters'] as $id => $chapter) if (!isset($chapters[$id])) $chapters[$id] = $chapter;
        foreach ((array)$incoming['choices'] as $id => $choice) $choices[$id] = $choice;
        $merged = cleanTraversee(['version' => 1, 'chapters' => $chapters, 'choices' => $choices]);
        $json = json_encode($merged, JSON_THROW_ON_ERROR);
        if (driver($db) === 'mysql') {
            dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), updated_at = VALUES(updated_at)', [$user['id'], 'traversee', $json, time()]);
        } else {
            dbQuery($db, 'INSERT INTO itp_states (user_id, state_key, data, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, state_key) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at', [$user['id'], 'traversee', $json, time()]);
        }
        $db->commit();
        output(['ok' => true, 'key' => 'traversee', 'data' => $merged, 'updated_at' => time()]);
    }
    if ($action === 'logout') {
        fields($input, []); resetSession(); output(['ok' => true, 'csrf' => $_SESSION['csrf'], 'user' => null]);
    }
    if ($action === 'oeuvres') {
        output(['ok' => true, 'connected' => true, 'territoires' => array_keys(ITP_TERRITOIRES), 'oeuvres' => itpWorksSummary($db, $config, $user)]);
    }
    if ($action === 'profile' && $method === 'GET') {
        output(['ok' => true, 'user' => publicUser($user), 'contexts' => accountSummary($db, $user['id'], $user)]);
    }
    if ($action === 'profile') {
        fields($input, ['display_name', 'avatar', 'interests']);
        [$name, $avatar, $interests] = cleanProfile($input, $db, $user['avatar']);
        dbQuery($db, 'UPDATE itp_users SET display_name = ?, avatar = ?, interests = ? WHERE id = ?', [$name, $avatar, $interests, $user['id']]);
        output(['ok' => true, 'user' => publicUser(loggedUser($db))]);
    }
    if ($action === 'password') {
        fields($input, ['current_password', 'new_password']);
        throttle($db, 'password', $user['id'], 6, 900, $config);
        if (!is_string($input['current_password'] ?? null) || strlen($input['current_password']) > 1024 || !password_verify(passwordMaterial($input['current_password'], $config), $user['password_hash'])) {
            fail(401, 'credentials', 'La phrase de passe actuelle est incorrecte.');
        }
        $hash = hashPassword(checkedPassword($input['new_password'] ?? null), $config);
        dbQuery($db, 'UPDATE itp_users SET password_hash = ?, auth_version = auth_version + 1 WHERE id = ?', [$hash, $user['id']]);
        resetSession(); $_SESSION['user_id'] = $user['id']; $_SESSION['auth_version'] = (int)$user['auth_version'] + 1;
        output(['ok' => true, 'csrf' => $_SESSION['csrf']]);
    }
    if ($action === 'invite') {
        fields($input, ['role']);
        $role = $input['role'] ?? 'member';
        if (!in_array($role, ['member', 'partner'], true)) fail(422, 'role', 'Ce type d’invitation n’est pas reconnu.');
        if ($user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administrateur du pilote.');
        throttle($db, 'invite', $user['id'], 20, 3600, $config);
        $token = bin2hex(random_bytes(24));
        dbQuery($db, 'INSERT INTO itp_invites (token_hash, role, created_at, expires_at) VALUES (?, ?, ?, ?)', [hash('sha256', $token), $role, time(), time() + 604800]);
        output(['ok' => true, 'invitation' => $token, 'role' => $role, 'expires_at' => time() + 604800], 201);
    }
    if ($action === 'feed' && ($_GET['context'] ?? '') === 'tous') {
        /* Communauté globale : les quatre univers membres, jamais l'espace partenaire. */
        $wanted = array_values(array_intersect(ITP_MEMBER_CONTEXTS, explode(',', is_string($_GET['univers'] ?? null) ? $_GET['univers'] : (isset($_GET['univers']) ? '' : implode(',', ITP_MEMBER_CONTEXTS)))));
        if (!$wanted) fail(422, 'context', 'Cet univers n’est pas reconnu.');
        $threads = feedThreads($db, $wanted, $user, 60);
        output(['ok' => true, 'context' => 'tous', 'univers' => $wanted, 'seen' => itpFeedSeen($db, $user['id'], $threads), 'threads' => $threads]);
    }
    if ($action === 'feed' && isset($_GET['territoire'])) {
        /* S1 : fil d'un territoire = contributions de toutes les œuvres inscrites dans ce territoire (principal ou secondaire),
         * chaque contribution restant rattachée à UNE œuvre. Jamais l'espace partenaire. */
        $terr = $_GET['territoire'];
        if (!is_string($terr) || !array_key_exists($terr, ITP_TERRITOIRES)) fail(422, 'territory', 'Ce territoire n’est pas reconnu.');
        $ids = []; $ctxs = [];
        foreach (itpWorks($config) as $w) if (in_array($terr, $w['territoires'], true) && in_array($w['universe'], ITP_MEMBER_CONTEXTS, true)) { $ids[] = $w['id']; $ctxs[$w['universe']] = true; }
        $threads = $ids ? feedThreads($db, array_keys($ctxs), $user, 60, null, $ids) : [];
        output(['ok' => true, 'territoire' => $terr, 'context' => 'territoire', 'oeuvres' => $ids, 'seen' => itpFeedSeen($db, $user['id'], $threads), 'threads' => $threads]);
    }
    if ($action === 'feed' && isset($_GET['oeuvre'])) {
        $work = itpWork($config, $_GET['oeuvre'], $user);
        $threads = feedThreads($db, [$work['universe']], $user, 40, $work);
        output(['ok' => true, 'context' => $work['universe'], 'oeuvre' => $work['id'], 'seen' => itpFeedSeen($db, $user['id'], $threads), 'threads' => $threads]);
    }
    if ($action === 'feed') {
        $ctx = context($_GET['context'] ?? null, $user);
        $threads = feedThreads($db, [$ctx], $user);
        output(['ok' => true, 'context' => $ctx, 'seen' => itpFeedSeen($db, $user['id'], $threads), 'threads' => $threads]);
    }
    if ($action === 'post') {
        fields($input, ['context', 'body', 'parent_id', 'request_key', 'chapter', 'owner_id', 'oeuvre']);
        /* R16.2 : publication liée strictement au compte où le brouillon a été composé. */
        assertContributionOwner($input['owner_id'] ?? null, $user);
        /* M2 : contribution rattachée à une œuvre ; sans « oeuvre », comportement v4 (œuvre historique, work_id NULL). */
        $postWork = null;
        if (array_key_exists('oeuvre', $input)) {
            $postWork = itpWork($config, $input['oeuvre'], $user, true);
            if (array_key_exists('context', $input) && $input['context'] !== $postWork['universe']) fail(422, 'work_context', 'Cette œuvre n’appartient pas à cet univers.');
            $ctx = $postWork['universe'];
            if ($postWork['legacy']) $postWork = null;
        } else {
            $ctx = context($input['context'] ?? null, $user);
        }
        /* S1 : un contexte sans œuvre historique (culture, societe) n'accepte que des contributions rattachées à une œuvre déclarée. */
        if (!$postWork && !isset(ITP_LEGACY_WORKS[$ctx])) fail(422, 'work_required', 'Cet univers ne propose que des œuvres déclarées : précisez l’œuvre.');
        $ideasMax = $postWork ? $postWork['idees'] : ITP_CONTEXTS[$ctx];
        $body = text($input['body'] ?? '', 20, 1000);
        $request = $input['request_key'] ?? '';
        if (!is_string($request) || !preg_match('/^[a-f0-9]{32,64}$/D', $request)) fail(422, 'request_key', 'La demande doit être renouvelée.');
        $parent = $input['parent_id'] ?? null;
        if ($parent !== null && (!is_string($parent) || !preg_match('/^[a-f0-9]{32}$/D', $parent))) fail(422, 'parent', 'Cette discussion n’existe pas.');
        $chapter = $input['chapter'] ?? null;
        if ($chapter !== null && (!is_int($chapter) || $chapter < 1 || $chapter > $ideasMax || $parent !== null)) fail(422, 'chapter', 'Cette idée du Long n’est pas reconnue.');
        $bodyHash = hash('sha256', $ctx . "\n" . ($parent ?? '') . "\n" . ($chapter ?? '') . "\n" . $body . ($postWork ? "\n" . $postWork['id'] : ''));
        $previous = dbQuery($db, 'SELECT id, body_hash, removed_at FROM itp_entries WHERE user_id = ? AND request_key = ?', [$user['id'], $request])->fetch();
        if ($previous) {
            assertActivePublicationRetry($previous, $bodyHash);
            output(['ok' => true, 'id' => $previous['id'], 'already_saved' => true]);
        }
        throttle($db, 'post', $user['id'], 12, 60, $config);
        $parentRow = $parent ? dbQuery($db, 'SELECT id, work_id FROM itp_entries WHERE id = ? AND parent_id IS NULL AND removed_at IS NULL AND context_id = ?', [$parent, $ctx])->fetch() : null;
        if ($parent && !$parentRow) {
            fail(404, 'parent', 'Cette discussion n’existe plus ou a été retirée.');
        }
        /* Une réponse appartient à l'œuvre de sa discussion : elle ne peut pas être rattachée à une autre œuvre. */
        if ($parentRow && array_key_exists('oeuvre', $input) && itpEntryWork($parentRow['work_id'], $ctx) !== itpEntryWork($postWork['id'] ?? null, $ctx)) fail(422, 'work_parent', 'Cette discussion concerne une autre œuvre.');
        $workId = $parentRow ? $parentRow['work_id'] : ($postWork['id'] ?? null);
        $id = bin2hex(random_bytes(16));
        try {
            dbQuery($db, 'INSERT INTO itp_entries (id, user_id, parent_id, body, created_at, request_key, body_hash, context_id, chapter, work_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [$id, $user['id'], $parent, $body, time(), $request, $bodyHash, $ctx, $chapter, $workId]);
        } catch (PDOException $e) {
            /* Two sessions may retry the same publication at the same instant. */
            if (!in_array((string)$e->getCode(), ['23000', '23505'], true)) throw $e;
            $previous = dbQuery($db, 'SELECT id, body_hash, removed_at FROM itp_entries WHERE user_id = ? AND request_key = ?', [$user['id'], $request])->fetch();
            if (!$previous) throw $e;
            assertActivePublicationRetry($previous, $bodyHash);
            output(['ok' => true, 'id' => $previous['id'], 'already_saved' => true]);
        }
        output(['ok' => true, 'id' => $id, 'already_saved' => false], 201);
    }
    if ($action === 'remove') {
        fields($input, ['id', 'owner_id']);
        assertActionOwner($input['owner_id'] ?? null, $user);
        $id = $input['id'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) fail(404, 'entry', 'Cette contribution n’existe pas.');
        $entry = dbQuery($db, 'SELECT user_id FROM itp_entries WHERE id = ?', [$id])->fetch();
        if (!$entry) fail(404, 'entry', 'Cette contribution n’existe pas.');
        if ($entry['user_id'] !== $user['id'] && $user['role'] !== 'admin') fail(403, 'owner_required', 'Vous pouvez retirer uniquement vos propres contributions.');
        dbQuery($db, 'UPDATE itp_entries SET body = ?, removed_at = ? WHERE id = ?', ['', time(), $id]);
        output(['ok' => true]);
    }
    if ($action === 'seen') {
        fields($input, ['context', 'owner_id', 'thread_ids']);
        assertContributionOwner($input['owner_id'] ?? null, $user);
        $ctx = context($input['context'] ?? null, $user);
        $ids = $input['thread_ids'] ?? null;
        if (!is_array($ids) || !array_is_list($ids) || count($ids) < 1 || count($ids) > 60)
            fail(422, 'thread_ids', 'Sélection de discussions invalide.');
        foreach ($ids as $id) if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id))
            fail(422, 'thread_ids', 'Identifiant de discussion invalide.');
        if (count(array_unique($ids)) !== count($ids)) fail(422, 'thread_ids', 'Discussions dupliquées.');
        /* Le serveur doit vérifier que chaque discussion exposée appartient réellement au contexte demandé.
         * Une erreur invalide la demande entière : aucune notification n'est effacée partiellement. */
        $marks = implode(',', array_fill(0, count($ids), '?'));
        $rows = dbQuery($db, "SELECT id, context_id, work_id FROM itp_entries WHERE parent_id IS NULL AND id IN ($marks)", $ids)->fetchAll();
        if (count($rows) !== count($ids)) fail(422, 'thread_ids', 'Une discussion n’est plus disponible.');
        $updates = [];
        foreach ($rows as $r) {
            if ($r['context_id'] !== $ctx || !in_array($ctx, ITP_MEMBER_CONTEXTS, true))
                fail(422, 'thread_context', 'Discussion hors du contexte sélectionné.');
            $work = itpEntryWork($r['work_id'], $ctx);
            if ($work === null) fail(422, 'thread_work', 'Œuvre de cette discussion non résolue.');
            $updates[] = [$user['id'], $r['id'], $work, time()];
        }
        $db->beginTransaction();
        foreach ($updates as $a) {
            if (driver($db) === 'mysql') dbQuery($db,
                'INSERT INTO itp_thread_reads (user_id, thread_id, work_id, seen_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE seen_at = GREATEST(seen_at, VALUES(seen_at)), work_id = VALUES(work_id)', $a);
            else dbQuery($db,
                'INSERT INTO itp_thread_reads (user_id, thread_id, work_id, seen_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, thread_id) DO UPDATE SET seen_at = MAX(itp_thread_reads.seen_at, excluded.seen_at), work_id = excluded.work_id', $a);
        }
        $db->commit();
        output(['ok' => true, 'seen_threads' => count($updates), 'contexts' => accountSummary($db, $user['id'], $user)]);
    }
    if ($action === 'progress') {
        fields($input, ['context', 'event', 'value', 'owner_id', 'oeuvre']);
        assertContributionOwner($input['owner_id'] ?? null, $user);
        /* M2 : « oeuvre » désigne l'œuvre ; sans elle (pages d'univers v4), l'œuvre historique de l'univers. */
        if (array_key_exists('oeuvre', $input)) {
            $work = itpWork($config, $input['oeuvre'], $user, true);
            if (array_key_exists('context', $input) && $input['context'] !== $work['universe']) fail(422, 'work_context', 'Cette œuvre n’appartient pas à cet univers.');
            $ctx = $work['universe'];
        } else {
            $ctx = context($input['context'] ?? null, $user);
            $work = itpLegacyWork($config, $ctx);
        }
        throttle($db, 'progress', $user['id'], 100, 60, $config);
        $event = $input['event'] ?? '';
        if (!in_array($event, [...ITP_STEPS, 'saved', 'note_k', 'idea'], true)) fail(422, 'progress', 'Cette étape n’est pas reconnue.');
        /* Sérialiser le compte et revalider sa session avant de lire ou écrire sa progression. */
        $db->beginTransaction();
        if (!itpProofSameAccount($db, $user)) {
            fail(401, 'login_required', 'Reconnectez-vous avant d’enregistrer votre progression.');
        }
        $progress = currentWorkProgress($db, $user['id'], $work);
        $newCredit = in_array($event, ['court_finished', 'long_finished'], true)
            ? !isset($progress['steps'][$event])
            : ($event === 'quiz_answered' && !is_array($progress['quiz'] ?? null));
        if (in_array($event, ITP_STEPS, true)) {
            if (in_array($event, ['court_finished', 'long_finished'], true) && !isset($progress['steps'][$event])) {
                $kind = $event === 'long_finished' ? 'long' : 'court';
                $min = $kind === 'long' ? itpWorkLongFloor($config, $work) : null;
                assertPlaybackFinish((array)($progress['steps'] ?? []), $event, $input['value'] ?? null, $ctx, null, $min);
                itpProofComplete($db, $config, $user, $work, $kind, $min ?? (ITP_MEDIA_TIMING['court'][$ctx] ?? 15));
            }
            if ($event === 'quiz_answered') {
                if ($work['quiz'] === null) fail(422, 'progress', 'Cette œuvre ne propose pas de quiz.');
                // Les démonstrateurs proposent le quiz dès le Court. Les autres œuvres le proposent après le Long.
                $steps = (array)($progress['steps'] ?? []);
                $lectureValidee = isset($steps['long_finished']) || ($work['legacy'] && isset($steps['court_finished']));
                // Une réponse déjà enregistrée reste acquise, y compris si elle précède ce contrôle.
                if (!is_array($progress['quiz'] ?? null) && !$lectureValidee) {
                    fail(409, 'quiz_requires_playback', $work['legacy']
                        ? 'Terminez le Court ou le Long de cette œuvre pour enregistrer votre réponse au quiz.'
                        : 'Terminez le Long de cette œuvre pour enregistrer votre réponse au quiz.');
                }
            }
            if (!isset($progress['steps'][$event])) $progress['steps'][$event] = time();
            /* Quiz : la première réponse fait foi (une seule attribution) ; la valeur est facultative pour les anciens clients. */
            if ($event === 'quiz_answered' && array_key_exists('value', $input) && !is_array($progress['quiz'] ?? null)) {
                if (!is_int($input['value']) || $input['value'] < 0 || $input['value'] > 2) fail(422, 'progress', 'Cette réponse n’est pas reconnue.');
                $progress['quiz'] = ['answer' => $input['value'], 'correct' => $input['value'] === $work['quiz'], 'at' => time()];
            }
        } elseif ($event === 'saved') {
            if (!is_bool($input['value'] ?? null)) fail(422, 'progress', 'La sélection n’est pas valide.');
            $progress['saved'] = $input['value'];
        } elseif ($event === 'idea') {
            /* 0 : « Aucune en particulier » ; 1 à 5 : idée du Long. */
            if (!is_int($input['value'] ?? null) || $input['value'] < 0 || $input['value'] > $work['idees']) fail(422, 'progress', 'Cette idée n’est pas reconnue.');
            $progress['idea'] = $input['value'];
        } else {
            if (!is_int($input['value'] ?? null) || $input['value'] < 1 || $input['value'] > 5) fail(422, 'progress', 'La Note K doit être comprise entre 1 et 5.');
            $progress['note_k'] = $input['value'];
        }
        $creditCreated = $newCredit && ($event !== 'quiz_answered' || is_array($progress['quiz'] ?? null));
        if ($creditCreated) {
            $kind = $event === 'court_finished' ? 'court' : 'long';
            $version = $event === 'quiz_answered'
                ? ($progress['credit_review']['long_finished']['media_version']
                    ?? $progress['credit_review']['court_finished']['media_version'] ?? null)
                : itpProofMedia($config, $work, $kind)['version'];
            $risks = itpCreditRisk($db, $user['id'], $work, $event, $progress);
            itpCreditQueue($progress, $event, $version, $risks);
        }
        if ($progress['steps'] === []) $progress['steps'] = (object)[];
        saveWorkProgress($db, $user['id'], $work, $progress);
        $db->commit();
        if ($itpCreditEvent !== null) {
            $review = $progress['credit_review'][$event] ?? null;
            $outcome = $creditCreated ? $review['status'] : ($newCredit ? 'no_credit' : 'unchanged');
            $reason = $creditCreated ? $review['history'][0]['reason'] : ($newCredit ? 'legacy_quiz_without_answer' : 'already_recorded');
            itpCreditAudit($itpRequestId, $itpCreditEvent, $outcome, $reason, 200);
        }
        output(['ok' => true, 'context' => $ctx, 'oeuvre' => $work['id'], 'progress' => itpCreditProgress($progress)]);
    }
    if ($action === 'delete_account') {
        /* RF-57 — Suppression du compte par la personne (21/10/2026). Effets : connexion impossible, profil anonymisé
         * (« Compte supprimé »), étapes, découvertes, positions, Traversée, codes et liens de récupération, signalements émis
         * supprimés ; texte des contributions effacé (repère « retirée » conservé dans les discussions, réponses des autres
         * personnes intactes). Les sauvegardes antérieures ne sont pas modifiées (voir mentions légales). */
        fields($input, ['current_password', 'confirm']);
        throttle($db, 'password', $user['id'], 6, 900, $config);
        if (($input['confirm'] ?? '') !== 'SUPPRIMER') fail(422, 'confirm', 'Saisissez SUPPRIMER pour confirmer.');
        if (!is_string($input['current_password'] ?? null) || strlen($input['current_password']) > 1024 || !password_verify(passwordMaterial($input['current_password'], $config), $user['password_hash'])) fail(401, 'credentials', 'La phrase de passe actuelle est incorrecte.');
        if ($user['role'] === 'admin') fail(409, 'admin_account', 'Le compte administrateur ne peut pas être supprimé depuis l’espace personnel (procédure privée).');
        $db->beginTransaction();
        $now = time(); $id = $user['id'];
        itpEcoDeleteAccount($db, $config, $id);
        if (itpGiftInstalled($db)) itpGiftDeleteAccount($db, $id);
        dbQuery($db, 'UPDATE itp_entries SET body = ?, removed_at = COALESCE(removed_at, ?) WHERE user_id = ?', ['', $now, $id]);
        foreach (['itp_work_progress', 'itp_progress2', 'itp_progress', 'itp_reads', 'itp_thread_reads', 'itp_states', 'itp_recovery'] as $t) dbQuery($db, "DELETE FROM $t WHERE user_id = ?", [$id]);
        dbQuery($db, 'DELETE FROM itp_reports WHERE reporter_id = ?', [$id]);
        dbQuery($db, 'UPDATE itp_users SET login = ?, display_name = ?, password_hash = ?, avatar = ?, interests = ?, role = ?, auth_version = auth_version + 1 WHERE id = ?',
            ['supprime-' . bin2hex(random_bytes(6)), 'Compte supprimé', hashPassword(bin2hex(random_bytes(32)), $config), 'nuit', '[]', 'deleted', $id]);
        $db->commit();
        resetSession();
        output(['ok' => true, 'deleted' => true, 'csrf' => $_SESSION['csrf']]);
    }
    if ($action === 'progression') {
        output(['ok' => true] + progression($db, $user['id'], $config));
    }
    if ($action === 'attenzia_agregats') {
        /* L20 : désactivé par défaut ; administrateur seul ; lecture seule. Voir itpAttenziaAgregats(). */
        if ($method !== 'GET') fail(405, 'method', 'Lecture seule.');
        if (($config['attenzia_agregats'] ?? false) !== true) fail(403, 'attenzia_disabled', 'Les agrégats ATTENZIA ne sont pas activés (décision juridique préalable).');
        if ($user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administrateur du pilote.');
        /* P1 : les différences entre lectures successives sont reproductibles sur le banc.
           Même si l’ancienne clé est modifiée, aucun agrégat ne sort d’une installation hors laboratoire. */
        if (!$local || ($config['attenzia_banc_synthetique'] ?? false) !== true) fail(403, 'attenzia_lab_only', 'Lecture réservée au banc synthétique local.');
        if (array_diff(array_keys($_GET), ['action'])) fail(422, 'attenzia_filter', 'Le banc utilise des contextes fixes, sans filtre.');
        throttle($db, 'attenzia', $user['id'], 30, 3600, $config);
        output(['ok' => true] + itpAttenziaAgregats($db, $config));
    }
    if ($action === 'react') {
        /* P4 T8 : reconnaissance d'une contribution. Ajout ou retrait d'une reconnaissance ; aucun Point, aucun XP. */
        fields($input, ['entry_id', 'kind', 'value', 'owner_id']);
        assertContributionOwner($input['owner_id'] ?? null, $user);
        $kind = $input['kind'] ?? null; $entryId = $input['entry_id'] ?? null; $value = $input['value'] ?? null;
        if (!is_string($kind) || !in_array($kind, ITP_REACTIONS, true)) fail(422, 'kind', 'Cette reconnaissance n’existe pas.');
        if (!is_string($entryId) || !preg_match('/^[a-f0-9]{32}$/D', $entryId)) fail(422, 'entry', 'Cette contribution n’existe pas.');
        if (!is_bool($value)) fail(422, 'value', 'La demande est incomplète.');
        $entry = dbQuery($db, 'SELECT id, user_id, context_id FROM itp_entries WHERE id = ? AND removed_at IS NULL', [$entryId])->fetch();
        if (!$entry || !in_array($entry['context_id'], allowedContexts($user), true)) fail(404, 'entry', 'Cette contribution n’existe plus ou a été retirée.');
        if (dbQuery($db, "SELECT 1 FROM itp_reports WHERE entry_id = ? AND status = 'retiree'", [$entryId])->fetch()) fail(404, 'entry', 'Cette contribution n’existe plus ou a été retirée.');
        if ($entry['user_id'] === $user['id']) fail(409, 'own_entry', 'Vous ne pouvez pas reconnaître votre propre contribution.');
        throttle($db, 'react', $user['id'], 60, 60, $config);
        itpEnsureReactions($db);
        $exists = (bool)dbQuery($db, 'SELECT 1 FROM itp_reactions WHERE entry_id = ? AND user_id = ? AND kind = ?', [$entryId, $user['id'], $kind])->fetch();
        if ($value && !$exists) {
            try { dbQuery($db, 'INSERT INTO itp_reactions (entry_id, user_id, kind, created_at) VALUES (?, ?, ?, ?)', [$entryId, $user['id'], $kind, time()]); } catch (PDOException $e) { /* doublon concurrent : l'état voulu est déjà atteint */ }
        } elseif (!$value && $exists) {
            dbQuery($db, 'DELETE FROM itp_reactions WHERE entry_id = ? AND user_id = ? AND kind = ?', [$entryId, $user['id'], $kind]);
        }
        $counts = ['utile' => 0, 'eclairant' => 0];
        foreach (dbQuery($db, 'SELECT kind, COUNT(*) AS n FROM itp_reactions WHERE entry_id = ? GROUP BY kind', [$entryId])->fetchAll() as $row) $counts[$row['kind']] = (int)$row['n'];
        $mine = array_column(dbQuery($db, 'SELECT kind FROM itp_reactions WHERE entry_id = ? AND user_id = ?', [$entryId, $user['id']])->fetchAll(), 'kind');
        output(['ok' => true, 'entry_id' => $entryId, 'reactions' => $counts, 'my_reactions' => $mine]);
    }
    if ($action === 'report') {
        fields($input, ['id', 'reason', 'owner_id']);
        assertActionOwner($input['owner_id'] ?? null, $user);
        throttle($db, 'report', $user['id'], 10, 3600, $config);
        $id = $input['id'] ?? ''; $reason = $input['reason'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) fail(404, 'entry', 'Cette contribution n’existe pas.');
        if (!is_string($reason) || !array_key_exists($reason, ITP_REPORT_REASONS)) fail(422, 'reason', 'Choisissez un motif de signalement.');
        $entry = dbQuery($db, 'SELECT user_id, context_id, removed_at FROM itp_entries WHERE id = ?', [$id])->fetch();
        if (!$entry || $entry['removed_at']) fail(404, 'entry', 'Cette contribution n’existe plus.');
        context($entry['context_id'], $user);
        if ($entry['user_id'] === $user['id']) fail(422, 'own_entry', 'Vous pouvez retirer vous-même votre contribution.');
        try {
            dbQuery($db, 'INSERT INTO itp_reports (id, entry_id, reporter_id, reason, created_at, status) VALUES (?, ?, ?, ?, ?, ?)', [bin2hex(random_bytes(16)), $id, $user['id'], $reason, time(), 'ouvert']);
        } catch (PDOException $e) {
            if (!in_array((string)$e->getCode(), ['23000', '23505'], true)) throw $e;
            output(['ok' => true, 'already_reported' => true]);
        }
        output(['ok' => true, 'already_reported' => false], 201);
    }
    if ($action === 'moderation') {
        /* L'administrateur voit le texte signalé, son univers, le motif et les noms affichés ; aucune autre donnée de compte. */
        if ($user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administrateur du pilote.');
        $rows = dbQuery($db, "SELECT r.entry_id, r.reason, MIN(r.created_at) AS first_at, COUNT(*) AS n, e.body, e.context_id, e.removed_at, e.created_at AS entry_at, u.display_name
            FROM itp_reports r JOIN itp_entries e ON e.id = r.entry_id JOIN itp_users u ON u.id = e.user_id
            WHERE r.status = 'ouvert' GROUP BY r.entry_id, r.reason, e.body, e.context_id, e.removed_at, e.created_at, u.display_name ORDER BY first_at ASC LIMIT 100")->fetchAll();
        output(['ok' => true, 'reasons' => ITP_REPORT_REASONS, 'reports' => array_map(fn($r) => ['entry_id' => $r['entry_id'], 'reason' => $r['reason'], 'count' => (int)$r['n'], 'first_at' => (int)$r['first_at'],
            'context' => $r['context_id'], 'author' => $r['display_name'], 'body' => $r['removed_at'] ? '' : $r['body'], 'removed' => (bool)$r['removed_at'], 'entry_at' => (int)$r['entry_at']], $rows)]);
    }
    if ($action === 'moderate') {
        fields($input, ['id', 'decision', 'owner_id']);
        assertActionOwner($input['owner_id'] ?? null, $user);
        if ($user['role'] !== 'admin') fail(403, 'admin_required', 'Cette action est réservée à l’administrateur du pilote.');
        $id = $input['id'] ?? ''; $decision = $input['decision'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) fail(404, 'entry', 'Cette contribution n’existe pas.');
        if (!in_array($decision, ['retirer', 'conserver'], true)) fail(422, 'decision', 'Décision non reconnue.');
        $db->beginTransaction();
        $n = dbQuery($db, "UPDATE itp_reports SET status = ?, decided_by = ?, decided_at = ? WHERE entry_id = ? AND status = 'ouvert'", [$decision === 'retirer' ? 'retiree' : 'conservee', $user['id'], time(), $id])->rowCount();
        if ($n === 0) { $db->rollBack(); fail(409, 'already_decided', 'Ce signalement a déjà été traité.'); }
        if ($decision === 'retirer') dbQuery($db, 'UPDATE itp_entries SET body = ?, removed_at = ? WHERE id = ? AND removed_at IS NULL', ['', time(), $id]);
        $db->commit();
        output(['ok' => true, 'decision' => $decision]);
    }
    fail(404, 'action', 'Cette action n’existe pas.');
} catch (PilotError $e) {
    if (isset($db) && $db->inTransaction()) $db->rollBack();
    if ($itpCreditEvent !== null) {
        itpCreditAudit($itpRequestId, $itpCreditEvent, 'refused', $e->kind, $e->status);
    }
    output(['ok' => false, 'error' => $e->kind, 'message' => $e->getMessage()], $e->status);
} catch (Throwable $e) {
    if (isset($db) && $db->inTransaction()) $db->rollBack();
    if ($itpCreditEvent !== null) {
        itpCreditAudit($itpRequestId, $itpCreditEvent, 'unavailable', 'runtime_or_storage', 503);
    }
    /* TECH-07 : cause technique journalisée (classe, code SQLSTATE/erreur, fichier:ligne, action) ; jamais le message de l'exception,
     * qui peut contenir des fragments de données. Aucune donnée personnelle ni identifiant de compte au journal. */
    $itpAction = (isset($_GET['action']) && is_string($_GET['action']) && preg_match('/^[a-z_]{1,40}$/D', $_GET['action'])) ? $_GET['action'] : '-';
    error_log(sprintf('ITHAKYA pilot: runtime or storage unavailable. rid=%s action=%s class=%s code=%s at=%s:%d', $itpRequestId, $itpAction,
        get_class($e), (string)$e->getCode(), basename($e->getFile()), $e->getLine()));
    output(['ok' => false, 'error' => 'unavailable', 'message' => 'Le pilote est momentanément indisponible. Votre texte n’est pas annoncé comme enregistré.'], 503);
}
