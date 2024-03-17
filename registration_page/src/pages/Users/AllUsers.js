import QueryEndpoint from "./QueryEndpoint";

function AllUsers(props) {
	const { handleRefresh, users } = QueryEndpoint(props["endpoint"], "GET");

	return (
		<div className="form-box">
			<div>
				<h1>All Users</h1>
				<button onClick={handleRefresh}>Refresh</button>
			</div>
			<div>
				{users !== '' && (
				<ul>
					{users.map((item, index) => (
						<li key={index}> {item} </li>
					))}
				</ul>
				)}
			</div>
		</div>
	);
}

export default AllUsers;