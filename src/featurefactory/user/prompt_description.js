var description = prompt("hello", "default");
var command = "commands._Session__description_store.set_description(" + description + ")";
console.log("Executing command " + command);
IPython.notebook.kernel.execute(command);
