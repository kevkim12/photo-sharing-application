let tags = [];
let textValue
let count = 1

function addTagInput() {
    const tagInput = document.createElement("input");
    tagInput.type = "text";
    tagInput.name = "tag" + count;
    tagInput.addEventListener('input', function() {
        textValue = this.value
    })
    tagholder.appendChild(tagInput)
    count++
}

const tagholder = document.querySelector("#tag-input")
