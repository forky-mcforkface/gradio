<script context="module" lang="ts">
	import type { FileData } from "@gradio/upload";
	export interface AudioData extends FileData {
		crop_min?: number;
		crop_max?: number;
	}
</script>

<script lang="ts">
	import { onDestroy, createEventDispatcher } from "svelte";
	import { Upload, ModifyUpload } from "@gradio/upload";
	//@ts-ignore
	import Range from "svelte-range-slider-pips";

	export let value: null | { name: string; data: string } = null;
	export let theme: string;
	export let name: string;
	export let source: "microphone" | "upload" | "none";
	export let drop_text: string = "Drop an audio file";
	export let or_text: string = "or";
	export let upload_text: string = "click to upload";

	let recording = false;
	let recorder: MediaRecorder;
	let mode = "";
	let audio_chunks: Array<Blob> = [];
	let audio_blob;
	let player;
	let inited = false;
	let crop_values = [0, 100];

	const dispatch = createEventDispatcher<{
		change: AudioData;
	}>();

	function blob_to_data_url(blob: Blob): Promise<string> {
		return new Promise((fulfill, reject) => {
			let reader = new FileReader();
			reader.onerror = reject;
			reader.onload = (e) => fulfill(reader.result as string);
			reader.readAsDataURL(blob);
		});
	}

	async function prepare_audio() {
		const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
		recorder = new MediaRecorder(stream);

		recorder.addEventListener("dataavailable", (event) => {
			audio_chunks.push(event.data);
		});

		recorder.addEventListener("stop", async () => {
			recording = false;
			audio_blob = new Blob(audio_chunks, { type: "audio/wav" });
			value = {
				data: await blob_to_data_url(audio_blob),
				name
			};
			dispatch("change", {
				data: await blob_to_data_url(audio_blob),
				name
			});
		});
	}

	async function record() {
		recording = true;
		audio_chunks = [];

		if (!inited) await prepare_audio();

		recorder.start();
	}

	onDestroy(() => {
		if (recorder && recorder.state !== "inactive") {
			recorder.stop();
		}
	});

	const stop = () => {
		recorder.stop();
	};

	function clear() {
		dispatch("change");
		mode = "";
		value = null;
	}

	function loaded(node: HTMLAudioElement) {
		function clamp_playback() {
			const start_time = (crop_values[0] / 100) * node.duration;
			const end_time = (crop_values[1] / 100) * node.duration;
			if (node.currentTime < start_time) {
				node.currentTime = start_time;
			}

			if (node.currentTime > end_time) {
				node.currentTime = start_time;
				node.pause();
			}
		}

		node.addEventListener("timeupdate", clamp_playback);

		return {
			destroy: () => node.removeEventListener("timeupdate", clamp_playback)
		};
	}

	function handle_change({
		detail: { values }
	}: {
		detail: { values: [number, number] };
	}) {
		if (!value?.data) return;

		dispatch("change", {
			data: value.data,
			name,
			crop_min: values[0],
			crop_max: values[1]
		});
	}

	function handle_load({
		detail
	}: {
		detail: { data: string; name: string; size: number; is_example: boolean };
	}) {
		value = detail;
		dispatch("change", { data: detail.data, name: detail.name });
	}
</script>

<div class="input-audio">
	{#if value === null}
		{#if source === "microphone"}
			{#if recording}
				<button
					class="p-2 rounded font-semibold bg-red-200 text-red-500 dark:bg-red-600 dark:text-red-100 shadow transition hover:shadow-md"
					on:click={stop}
				>
					Stop Recording
				</button>
			{:else}
				<button
					class="p-2 rounded font-semibold shadow transition hover:shadow-md bg-white dark:bg-gray-800"
					on:click={record}
				>
					Record
				</button>
			{/if}
		{:else if source === "upload"}
			<Upload filetype="audio/*" on:load={handle_load} {theme}>
				{drop_text}
				<br />- {or_text} -<br />
				{upload_text}
			</Upload>
		{/if}
	{:else}
		<ModifyUpload
			on:clear={clear}
			on:edit={() => (mode = "edit")}
			editable
			absolute={false}
			{theme}
		/>

		<audio
			use:loaded
			class="w-full"
			controls
			bind:this={player}
			preload="metadata"
			src={value.data}
		/>

		{#if mode === "edit" && player?.duration}
			<Range
				bind:values={crop_values}
				range
				min={0}
				max={100}
				step={1}
				on:change={handle_change}
			/>
		{/if}
	{/if}
</div>