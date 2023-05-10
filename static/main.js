document.addEventListener('DOMContentLoaded', function(){
const words_tab = document.getElementById('words_tab')
const brands_tab = document.getElementById('brands_tab')

const words_table = document.getElementById('words_table')
const brands_table = document.getElementById('brands_table')
// console.log('sdsdsd',words_tab)


words_tab.addEventListener("click", (event) => {
    words_table.classList.remove("hidden");
    words_tab.classList.add('text-indigo-500', 'border-indigo-500');
    brands_tab.classList.remove('text-indigo-500', 'border-indigo-500');
    brands_table.classList.add("hidden");
  });

  brands_tab.addEventListener("click", (event) => {
    brands_table.classList.remove("hidden");
    brands_tab.classList.add('text-indigo-500', 'border-indigo-500');
    words_tab.classList.remove('text-indigo-500', 'border-indigo-500');
    words_table.classList.add("hidden");
  });

});





    //  $("body").on("click",function(yy){
    $(document).ready(function() {

        const progressBox = document.getElementById('progress-box')
        const TableStop = document.getElementById('progress-box')
        const csrf_words = document.querySelector("#example input[name='csrfmiddlewaretoken'");
        const csrf_bd = document.querySelector("#example5 input[name='csrfmiddlewaretoken'");
        const csrf_price = document.querySelector("#example4 input[name='csrfmiddlewaretoken'");
        const csrf_brand = document.querySelector("#example2 input[name='csrfmiddlewaretoken'");
    // console.log(csrf_bd)
    $("#stopwords-form").submit(function (e) {

        e.preventDefault();
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // Ajax Call

        $.ajax({
            type: 'POST',
            url: "/",
            data: serializedData,
			// handle a successful response
            success: function (response) {
                // On successful, clear all form data
                $("#stopwords-form").trigger('reset');

                // Display new participant to table
                var instance = JSON.parse(response["instance"]);
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example tbody").prepend(
                   `<tr class="post-${pk}">
                    <td class="text-center sorting_1">${fields["words"]||""}</td>
                    <td class="text-center sorting_1">
                         <input type="hidden" name="csrfmiddlewaretoken" value="">
                          <button type="button"  class="delete_words" data-id='${pk}' > 
                          
                          <svg width="22" height="22" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path fill-rule="evenodd" clip-rule="evenodd" d="M8 15H40L37 44H11L8 15Z" fill="#EB5757" stroke="#1D1D1D" stroke-width="3" stroke-linejoin="round"/>
                          <path d="M20.002 25.0024V35.0026M28.0024 24.9995V34.9972" stroke="#E0E0E0" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M12 14.9999L28.3242 3L36 15" stroke="#1D1D1D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                          
                          </button>
                        </td> 
                    </tr>`
                )
            },     
         
            error: function (response) {
                // alert non successful response
                alert(response["responseJSON"]["error"]);
            }
        });
    });  

 
    $("body").on("click",".delete_words",function(u){
        console.log('удалили')
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delete/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_words.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_words.value );
                },
                success: function(response){
                    $("#example .post-" + id).remove();
                }
            });
        });  


        $("body").on("click",".delete_bd",function(u){

                u.preventDefault();
                var id = $(this).data('id');

                $.ajax({
                    url: "bddel/"+id,
                    type: 'DELETE',
                    dataType: 'json',
                    headers: {
                        "X-CSRFTOKEN": csrf_bd.value
                    },
                    data: { id : id },

                    beforeSend: function(xhr) {
                        xhr.setRequestHeader("X-CSRFToken", csrf_bd.value );
                    },
                    success: function(response){
                        
                        $("#example5 .post-" + id).remove();
                    },
                    error: function (response) {
                        
                        console.log(response,'произошла ошибка')
                     }
                });
            });
    

    $("#brand-form").submit(function (z) {
        // preventing default actions
        z.preventDefault();
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // Ajax Call
        $.ajax({
            type: 'POST',
            url: "/",
            data: serializedData,
			// handle a successful response
            success: function (response) {
                // On successful, clear all form data
                $("#brand-form").trigger('reset');

                // Display new participant to table
                var instance = JSON.parse(response["instance"]);
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example2 tbody").prepend(
                   `<tr class="post-${pk}">
                    <td class="text-center sorting_1">${fields["brand"]||""}</td>
                    <td class="text-center sorting_1">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrf_brand.value}">
                    <button type="button"  class="delete_buttonbr" data-id='${pk}' > 
                    
                    <svg width="22" height="22" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" clip-rule="evenodd" d="M8 15H40L37 44H11L8 15Z" fill="#EB5757" stroke="#1D1D1D" stroke-width="3" stroke-linejoin="round"/>
                    <path d="M20.002 25.0024V35.0026M28.0024 24.9995V34.9972" stroke="#E0E0E0" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 14.9999L28.3242 3L36 15" stroke="#1D1D1D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                    
                    
                    </button>
                        </td>
                    </tr>`
                );
            },     
         
            error: function (response) {
                // alert non successful response
                alert(response["responseJSON"]["error"]);
            }
        });
    });

    $("#price-forms").submit(function (a) {
        progressBox.classList.remove('not-visible')
        // preventing default actions
        a.preventDefault();
        $form = $(this);
        var formData = new FormData(this);
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // console.log(serializedData);
        // Ajax Call
        $.ajax({
            type: 'POST',
            url: "/",
            data: formData,

            xhr: function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    // console.log(e)
                    if (e.lengthComputable) {
                        const percent = e.loaded / e.total * 100
                        console.log(percent)
                        progressBox.innerHTML = `
                        <div class="h-1 bg-blue-500" style="width:${percent}%"></div>`
                    }
                })
                    return xhr
            },

            success: function (response) {
                progressBox.classList.add('not-visible')
                $("#price-forms").trigger('reset');
                var instance = JSON.parse(response["instance"]);
                var data = (response["data"]);
                // console.log('fgfgfg',data)
                var fields = instance[0]["fields"];
                var pk = instance[0]["pk"];
                $("#example4 tbody").prepend(
                   `<tr class="post-${data["pk"]}">
                    <td class="text-center sorting_1">${fields["files"]||""}</td>
                    <td class="text-center sorting_1">${data["brend_field"]||""}</td>
                    <td class="text-center sorting_1">${data["currency_field"]||""}</td>

                    <td class="text-center sorting_1">
                    <input type="hidden" name="csrfmiddlewaretoken" value="">
                            <button type="button"  class="delete_price" data-id="${data["pk"]}" > 
                            
                            <svg width="22" height="22" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path fill-rule="evenodd" clip-rule="evenodd" d="M8 15H40L37 44H11L8 15Z" fill="#EB5757" stroke="#1D1D1D" stroke-width="3" stroke-linejoin="round"/>
                            <path d="M20.002 25.0024V35.0026M28.0024 24.9995V34.9972" stroke="#E0E0E0" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M12 14.9999L28.3242 3L36 15" stroke="#1D1D1D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                            
                            </button>
                    </td>

                    <td class="text-center sorting_1">
                    <input type="hidden" name="csrfmiddlewaretoken" value="">

                    <a href="/lcreatepr/${data["pk"]}" class="inline-flex items-center" data-id="${data["pk"]}">
                        <img alt="blog" src="https://svgshare.com/i/szx.svg" class="w-8 h-8 rounded-full flex-shrink-0 object-cover object-center">
                        <span class="flex-grow flex flex-col pl-3">
                        <span class="title-font font-medium text-gray-900">Сформировать</span>
                        </span>
                    </a>
                           
                    </td>

                    </tr>`
                );
                
             },
             error: function (response) {
                console.log(response,'произошла ошибка')
             },
            cache: false,
            contentType: false,
            processData: false
        });
    });
   
    $("body").on("click",".delete_buttonbr",function(u){
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delbr/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_brand.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_brand.value );
                },
                success: function(response){
                    $("#example2 .post-" + id).remove();
                }
            });
        });


        $("body").on("click",".delete_price",function(u){
            u.preventDefault();
            var id = $(this).data('id');
            $.ajax({
                url: "delpr/"+id,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    "X-CSRFTOKEN": csrf_price.value
                },
                data: { id : id },
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_price.value );
                },
                success: function(response){
                    $("#example4 .post-" + id).remove();
                }
            });
        });

        // $("body").on("click",".load_price",function(u){
        //     u.preventDefault();
        //     var id = $(this).data('id');
        //     $.ajax({
        //         url: "loadpr/"+id,
        //         type: 'GET',
        //         data: 'json',  
        //         headers: {
        //             "X-CSRFTOKEN": csrf_price.value
        //         },
        //         data: { id : id },
        //         beforeSend: function(xhr) {
        //             xhr.setRequestHeader("X-CSRFToken", csrf_price.value );
        //         },
        //         success: function(response){
        //             console.log(response,'ВСЕ ХОРОШО, ПРАЙС ВЫГРУЖАЕТСЯ')
        //         },
        //         error: function (response) {
        //             console.log(response,'произошла ошибка')
        //          }
        //     });
        // });

    });