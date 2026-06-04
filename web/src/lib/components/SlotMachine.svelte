<script>
	let { teamName, decade, spinning = false } = $props();
</script>

<div class="lower3" class:spinning>
	<div class="flag">
		<span class="flabel">{spinning ? '· · ·' : 'ON THE\nCLOCK'}</span>
	</div>
	<div class="body">
		<span class="decade">{decade}</span>
		<span class="team">{teamName}</span>
	</div>
	<div class="sheen"></div>
</div>

<style>
	.lower3 {
		position: relative;
		display: flex;
		align-items: stretch;
		border-radius: 9px;
		overflow: hidden;
		border: 1px solid var(--line-2);
		border-top-color: var(--line-3);
		box-shadow:
			inset 0 1px 0 rgba(255, 255, 255, 0.18),
			var(--shadow);
		background:
			linear-gradient(180deg, rgba(255, 240, 214, 0.13), rgba(255, 240, 214, 0) 46%),
			linear-gradient(180deg, #1c405e, #0c1f30);
	}
	.flag {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 12px;
		background: linear-gradient(180deg, #ff3a47, #c5141f);
		border-right: 1px solid rgba(0, 0, 0, 0.35);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
		min-width: 74px;
	}
	.flabel {
		font-family: var(--display);
		font-weight: 800;
		font-size: 0.72rem;
		line-height: 1;
		letter-spacing: 0.06em;
		color: #fff;
		text-align: center;
		white-space: pre-line;
		text-shadow: 0 1px 1px rgba(0, 0, 0, 0.35);
	}
	.body {
		flex: 1;
		min-width: 0;
		padding: 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 1px;
		text-align: left;
	}
	.decade {
		font-family: var(--display);
		font-weight: 600;
		font-style: italic;
		font-size: 0.95rem;
		letter-spacing: 0.04em;
		color: var(--gold-bright);
	}
	.team {
		font-family: var(--display);
		font-weight: 800;
		font-size: clamp(1.5rem, 7.5vw, 2rem);
		line-height: 1;
		text-transform: uppercase;
		letter-spacing: 0.01em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		background: linear-gradient(180deg, #fff7e6, #e7d2a8 60%, #c2a878);
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
		text-shadow:
			-1px 0 rgba(216, 35, 42, 0.35),
			1px 0 rgba(70, 174, 191, 0.3);
	}
	.sheen {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 40%;
		left: -60%;
		background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.18), transparent);
		transform: skewX(-18deg);
	}
	.spinning .sheen {
		animation: sweep 0.7s linear infinite;
	}
	.spinning .team {
		filter: blur(4px);
		opacity: 0.85;
	}
	@keyframes sweep {
		to {
			left: 120%;
		}
	}
</style>
