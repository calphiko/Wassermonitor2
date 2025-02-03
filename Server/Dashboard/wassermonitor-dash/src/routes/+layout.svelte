<script>import Header from './Header.svelte';
import '../app.css';

/** @type {{children: import('svelte').Snippet}} */
let { children } = $props();</script>

<div class="bg-sky-50 dark:bg-gray-900 flex justify-center " >
    <div class="app bg-sky-100 border dark:border-0 dark:bg-gray-800  sm:w-3/4 p-0 m-0">

        <main class="" >
            {@render children()}
        </main>

        <footer>
            <p class="text-center bg-yellow-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500 h-20 my-5">
                build with <a href="https://svelte.dev/docs/kit">svelte</a><br>
                if you are interested in wassermonitor please visit my <a href="https://wassermonitor.de">blog</a>.
            </p>
        </footer>

    </div>
</div>


<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100%;
		justify-content: center;

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
