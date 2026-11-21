<?php
declare(strict_types=1);
if (!defined('ITP_SCHEMA')) { http_response_code(404); exit; }

const ITP_CREDIT_EVENTS = ['court_finished', 'long_finished', 'quiz_answered'];

function itpCreditAudit(string $requestId, string $event, string $outcome, string $reason, int $status): void {
    // Le journal d’exploitation est corrélé à la décision HTTP sans identité de compte ni corps de requête.
    if (!preg_match('/^[a-z][a-z0-9_]{0,63}$/D', $reason)) $reason = 'unspecified';
    error_log(sprintf('ITHAKYA credit: rid=%s event=%s outcome=%s reason=%s http=%d',
        $requestId, $event, $outcome, $reason, $status));
}

/* Les faits de parcours sont conservés. Seule une décision serveur autorisée
 * confirme les crédits, automatiquement si les contrôles serveur sont satisfaits.
 * Les séquences contradictoires restent en attente. Les faits historiques sans marqueur
 * restent acquis et ne valent aucune nouvelle qualification de présence humaine. */
function itpCreditPublic(array $reviews): array {
    $out = [];
    foreach ($reviews as $event => $review) {
        $out[$event] = array_intersect_key($review, array_flip([
            'status', 'revision', 'requested_at', 'decided_at', 'reason', 'policy_version', 'qualification', 'economic_eligible'
        ]));
    }
    return $out;
}
function itpCreditProgress(array $progress): array {
    $progress['credit_review'] = itpCreditPublic($progress['credit_review'] ?? []);
    return $progress;
}
function itpCreditStatus(array $data, string $event): string {
    return $data['credit_review'][$event]['status'] ?? 'legacy';
}
function itpCreditRisk(PDO $db, string $user, array $work, string $event, array $progress): array {
    if ($event === 'quiz_answered') {
        foreach (['court_finished', 'long_finished'] as $step) {
            $status = itpCreditStatus($progress, $step);
            if (!in_array($status, ['legacy', 'confirmed'], true)) return ['prerequisite_under_review'];
        }
        return [];
    }
    $kind = $event === 'court_finished' ? 'court' : 'long';
    $key = itpProofClockKey($work, $kind);
    $current = readState($db, $user, $key)['data']['elapsed'] ?? [];
    foreach (dbQuery($db, "SELECT state_key, data FROM itp_states
        WHERE user_id = ? AND state_key LIKE 'ls-%'", [$user])->fetchAll() as $row) {
        if ($row['state_key'] === $key) continue;
        $other = json_decode($row['data'], true, 16, JSON_THROW_ON_ERROR)['elapsed'] ?? [];
        $overlap = 0;
        foreach ($current as [$start, $end]) {
            foreach ($other as [$lo, $hi]) $overlap += max(0, min($end, $hi) - max($start, $lo));
        }
        // Les préchargements et les pauses ne produisent pas ces intervalles.
        if ($overlap >= 1500) return ['overlapping_technical_sessions'];
    }
    return [];
}
function itpCreditQueue(array &$progress, string $event, ?string $version, array $risks): void {
    if (isset($progress['credit_review'][$event])) return;
    $now = time();
    $status = $risks ? 'pending' : 'confirmed';
    $progress['credit_review'][$event] = [
        'policy_version' => ITP_PILOT_POLICY, 'qualification' => 'usage_telemetry_only', 'economic_eligible' => false,
        'status' => $status, 'risks' => $risks, 'revision' => 1, 'key' => bin2hex(random_bytes(16)),
        'requested_at' => $now, 'decided_at' => $risks ? null : $now, 'media_version' => $version, 'history' => [
            ['status' => $status, 'at' => $now, 'by' => null, 'reason' => $risks ? implode(',', $risks) : 'automatic_server_usage_v035']
        ]
    ];
}
function itpCreditHandle(PDO $db, array $config, ?array $user, string $action, array $input): void {
    if (!in_array($action, ['lecture_reviews', 'lecture_decide'], true)) return;
    $admin = authenticated($user);
    if ($admin['role'] !== 'admin') fail(403, 'admin_required', 'Cette décision est réservée à l’administration.');
    if ($action === 'lecture_reviews') {
        $page = filter_var($_GET['page'] ?? 1, FILTER_VALIDATE_INT);
        if ($page === false || $page < 1 || $page > 100000) fail(422, 'pagination', 'Page invalide.');
        $offset = ($page - 1) * 100;
        $rows = dbQuery($db, 'SELECT p.user_id, p.work_id, p.universe_id, p.data, u.login
            FROM itp_work_progress p JOIN itp_users u ON u.id = p.user_id
            WHERE p.data LIKE ? ORDER BY p.user_id, p.work_id LIMIT 100 OFFSET ' . $offset,
            ['%"credit_review"%'])->fetchAll();
        $items = [];
        foreach ($rows as $row) {
            $data = json_decode($row['data'], true, 16, JSON_THROW_ON_ERROR);
            foreach (($data['credit_review'] ?? []) as $event => $review) {
                $items[] = ['member_id' => $row['user_id'], 'login' => $row['login'],
                    'oeuvre' => $row['work_id'], 'context' => $row['universe_id'], 'event' => $event,
                    'review' => $review];
            }
        }
        output(['ok' => true, 'items' => $items, 'page' => $page, 'has_more' => count($rows) === 100]);
    }
    fields($input, ['owner_id', 'member_id', 'oeuvre', 'event', 'review_key', 'expected_revision',
        'decision_key', 'decision', 'proof_ref', 'reason']);
    assertActionOwner($input['owner_id'] ?? null, $admin);
    $member = $input['member_id'] ?? null;
    $event = $input['event'] ?? null;
    $key = $input['review_key'] ?? null;
    $operation = $input['decision_key'] ?? null;
    $revision = $input['expected_revision'] ?? null;
    $decision = $input['decision'] ?? null;
    if (!is_string($member) || !preg_match('/^[a-f0-9]{32}$/D', $member)
        || !in_array($event, ['court_finished', 'long_finished', 'quiz_answered'], true)
        || !is_string($key) || !preg_match('/^[a-f0-9]{32}$/D', $key)
        || !is_string($operation) || !preg_match('/^[a-f0-9]{32}$/D', $operation)
        || !is_int($revision) || $revision < 1
        || !in_array($decision, ['confirmed', 'rejected', 'cancelled', 'pending'], true)) {
        fail(422, 'credit_review', 'Décision de crédit invalide.');
    }
    $reference = text($input['proof_ref'] ?? null, 6, 120);
    $reason = text($input['reason'] ?? null, 10, 240);
    $work = itpWork($config, $input['oeuvre'] ?? null, $admin, true);
    $fingerprint = hash('sha256', json_encode([$decision, $revision, $reference, $reason], JSON_THROW_ON_ERROR));
    $transitions = ['pending' => ['confirmed', 'rejected'], 'confirmed' => ['cancelled'],
        'rejected' => ['pending'], 'cancelled' => ['pending']];
    $db->beginTransaction();
    try {
        if (!itpProofSameAccount($db, $admin)) fail(401, 'login_required', 'Reconnectez-vous avant cette décision.');
        $lock = 'SELECT id FROM itp_users WHERE id = ?';
        if (driver($db) === 'mysql') $lock .= ' FOR UPDATE';
        else dbQuery($db, 'UPDATE itp_users SET auth_version = auth_version WHERE id = ?', [$member]);
        if (!dbQuery($db, $lock, [$member])->fetchColumn()) fail(404, 'member', 'Compte introuvable.');
        $progress = currentWorkProgress($db, $member, $work);
        $review = $progress['credit_review'][$event] ?? null;
        if (!is_array($review) || !hash_equals($review['key'], $key)) fail(409, 'credit_review', 'Ce crédit ne correspond plus à cette demande.');
        foreach (($review['history'] ?? []) as $old) {
            if (($old['decision_key'] ?? null) !== $operation) continue;
            if (!hash_equals($old['fingerprint'], $fingerprint)) fail(409, 'idempotency_conflict', 'Cette opération a déjà servi à une autre décision.');
            $db->commit();
            output(['ok' => true, 'already_recorded' => true, 'review' => itpCreditPublic([$event => $review])[$event]]);
        }
        if ($review['revision'] !== $revision
            || !in_array($decision, $transitions[$review['status']] ?? [], true)) {
            fail(409, 'credit_review_changed', 'Ce crédit a changé. Relisez son état avant de décider.');
        }
        $eligible = static function (string $step) use ($progress): bool {
            return isset($progress['steps'][$step])
                && in_array(itpCreditStatus($progress, $step), ['legacy', 'confirmed'], true);
        };
        if ($decision === 'confirmed' && $event === 'quiz_answered'
            && !$eligible('court_finished') && !$eligible('long_finished')) {
            fail(409, 'credit_prerequisite', 'Confirmez la lecture requise avant les crédits du quiz.');
        }
        if ($decision === 'cancelled' && $event !== 'quiz_answered'
            && $eligible('quiz_answered')) {
            $other = $event === 'court_finished' ? 'long_finished' : 'court_finished';
            if (!$eligible($other)) fail(409, 'credit_dependency', 'Les crédits du quiz dépendent encore de cette lecture.');
        }
        if (count($review['history']) >= 128) fail(409, 'credit_review_history', 'L’historique de cette demande doit être examiné.');
        $review['status'] = $decision;
        $review['revision']++;
        $review['decided_at'] = time();
        $review['reason'] = $reason;
        $review['history'][] = ['status' => $decision, 'at' => $review['decided_at'],
            'by' => $admin['id'], 'proof_ref' => $reference, 'reason' => $reason,
            'decision_key' => $operation, 'fingerprint' => $fingerprint];
        $progress['credit_review'][$event] = $review;
        saveWorkProgress($db, $member, $work, $progress);
        if ($decision === 'cancelled' && itpGiftInstalled($db)) {
            $used = (int)dbQuery($db, "SELECT COALESCE(SUM(points_cost), 0) FROM itp_gift_claims
                WHERE user_id = ? AND status IN ('reserved','delivered')", [$member])->fetchColumn();
            if (progression($db, $member)['points'] < $used) {
                $db->rollBack();
                fail(409, 'credit_in_use', 'Régularisez les récompenses engagées avant cette annulation.');
            }
        }
        $db->commit();
        output(['ok' => true, 'already_recorded' => false,
            'review' => itpCreditPublic([$event => $review])[$event]]);
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}
