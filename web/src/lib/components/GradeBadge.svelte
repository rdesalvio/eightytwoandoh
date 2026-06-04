<script>
	let { grade, label, color, record, perfect = false } = $props();
</script>

<div class="badge" class:perfect style="--c:{color}">
	<div class="bug">
		<span class="record">{record}</span>
	</div>
	<div class="accent"></div>
	<div class="meta">
		<span class="grade">{grade}</span>
		<span class="label">{label}</span>
	</div>
</div>

<style>
	.badge {
		text-align: center;
		padding: 2px 0;
	}
	.bug {
		display: inline-block;
		padding: 2px 4px;
	}
	.record {
		font-family: var(--score);
		font-weight: 600;
		font-size: clamp(4.4rem, 25vw, 7rem);
		line-height: 0.8;
		letter-spacing: 0.01em;
		font-variant-numeric: tabular-nums;
		background: linear-gradient(180deg, #fff8ea 0%, #f1ddae 46%, #cba87a 62%, #fff2d6 100%);
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
		text-shadow:
			-1.5px 0 rgba(216, 35, 42, 0.5),
			1.5px 0 rgba(70, 174, 191, 0.45);
		filter: drop-shadow(0 2px 0 rgba(0, 0, 0, 0.4)) drop-shadow(0 0 24px rgba(232, 163, 61, 0.45));
	}
	.accent {
		width: 132px;
		height: 4px;
		margin: 8px auto 0;
		border-radius: 3px;
		background: linear-gradient(90deg, transparent, var(--red), transparent);
	}
	.meta {
		display: inline-flex;
		align-items: center;
		gap: 9px;
		margin-top: 12px;
	}
	.grade {
		font-family: var(--display);
		font-weight: 800;
		font-size: 1.4rem;
		color: var(--c);
		border: 1.5px solid var(--c);
		border-radius: 6px;
		padding: 1px 11px;
		line-height: 1.25;
		background: color-mix(in srgb, var(--c) 14%, transparent);
		box-shadow:
			inset 0 1px 0 rgba(255, 255, 255, 0.2),
			0 0 18px color-mix(in srgb, var(--c) 30%, transparent);
	}
	.label {
		font-family: var(--display);
		text-transform: uppercase;
		letter-spacing: 0.14em;
		font-size: 0.84rem;
		font-weight: 700;
		color: var(--c);
	}
	.perfect .record {
		background: linear-gradient(180deg, #fff7e0 0%, #ffd966 48%, #e0a01f 64%, #fff2cf 100%);
		-webkit-background-clip: text;
		background-clip: text;
		filter: drop-shadow(0 2px 0 rgba(0, 0, 0, 0.35)) drop-shadow(0 0 26px rgba(255, 206, 84, 0.55));
	}
</style>
