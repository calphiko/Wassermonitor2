<script>import Header from './Header.svelte';
import '../app.css';

/** @type {{children: import('svelte').Snippet}} */
let { children } = $props();</script>


<div class="app">
	<Header></Header>

	<main>
		{@render children()}
	</main>

	<footer>
		<p>
			build with <a href="https://svelte.dev/docs/kit">svelte</a>
		</p>
		<p>
			if you are interested in wassermonitor please my <a href="https://wassermonitor.de">blog</a>.
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
