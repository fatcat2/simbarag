import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

import "./App.css";

const App = () => {
	const [query, setQuery] = useState<string>("");
	const [answer, setAnswer] = useState<string>("");
	const [loading, setLoading] = useState<boolean>(false);
	const [simbaMode, setSimbaMode] = useState<boolean>(false);

	const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

	const handleQuestionSubmit = () => {
		if (simbaMode) {
			console.log("simba mode activated");
			setLoading(true);
			const randomIndex = Math.floor(Math.random() * simbaAnswers.length);
			const randomElement = simbaAnswers[randomIndex];
			setAnswer(randomElement);
			setTimeout(() => setLoading(false), 3500);
			return;
		}
		const payload = { query: query };
		setLoading(true);
		axios
			.post("/api/query", payload)
			.then((result) => setAnswer(result.data.response))
			.finally(() => setLoading(false));
	};
	const handleQueryChange = (event) => {
		setQuery(event.target.value);
	};
	return (
		<div className="flex flex-row justify-center py-4">
			<div className="flex flex-col gap-4 min-w-xl max-w-xl">
				<div className="flex flex-row justify-center gap-2 grow">
					<h1 className="text-3xl">ask simba!</h1>
				</div>
				<div className="flex flex-row justify-between gap-2 grow">
					<textarea
						type="text"
						className="p-4 border border-blue-200 rounded-md grow"
						onChange={handleQueryChange}
					/>
				</div>
				<div className="flex flex-row justify-between gap-2 grow">
					<button
						className="p-4 border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow"
						onClick={() => handleQuestionSubmit()}
						type="submit"
					>
						Submit
					</button>
				</div>
				<div className="flex flex-row justify-center gap-2 grow">
					<input
						type="checkbox"
						onChange={(event) => setSimbaMode(event.target.checked)}
					/>
					<p>simba mode?</p>
				</div>
				{loading ? (
					<div className="flex flex-col w-full animate-pulse gap-2">
						<div className="flex flex-row gap-2 w-full">
							<div className="bg-gray-400 w-1/2 p-3 rounded-lg" />
							<div className="bg-gray-400 w-1/2 p-3 rounded-lg" />
						</div>
						<div className="flex flex-row gap-2 w-full">
							<div className="bg-gray-400 w-1/3 p-3 rounded-lg" />
							<div className="bg-gray-400 w-2/3 p-3 rounded-lg" />
						</div>
					</div>
				) : (
					<div className="flex flex-col">
						<ReactMarkdown>{answer}</ReactMarkdown>
					</div>
				)}
			</div>
		</div>
	);
};

export default App;
