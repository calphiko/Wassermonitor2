<script>
import { onMount } from 'svelte';
import Header from './Header.svelte';
import '../app.css';

/** @type {{children: import('svelte').Snippet}} */
let { children } = $props();

onMount(() => {
	document.documentElement.classList.add('dark');
	document.documentElement.setAttribute('data-theme', 'wintry');
});
</script>

<div class="app theme-wintry" data-theme="wintry">
	<Header></Header>

	<main>
		{@render children()}
	</main>

	<footer>
		<p class="text-center bg-surface-900/80 text-surface-100 text-sm rounded-xl block p-3 my-5 shadow-lg shadow-slate-950/40">
			 <a target="_blank" href="https://pakleds-patentoffice.de">Pakleds Patentoffice</a>
	    </p>
	</footer>
</div>


<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		width: 100%;
		max-width: 64rem;
		margin: 0 auto;
		box-sizing: border-box;
	}

	footer {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 12px;
	}

	footer a {
		font-weight: bold;
	}

	@media (min-width: 480px) {
		footer {
			padding: 12px 0;
		}
	}
</style>
