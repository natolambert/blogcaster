These images were generated with the text from `examples/experimental`, with the following calls:

```
get_image(0, prompts[2], title, vivid=True, hd=False, rewrite=False, no_sleep=True)
get_image(1, prompts[2], title, vivid=False, hd=False, rewrite=False, no_sleep=True)
get_image(2, prompts[2], title, vivid=True, hd=False, rewrite=True, no_sleep=True)
get_image(3, prompts[2], title, vivid=False, hd=False, rewrite=True, no_sleep=True)

get_image(4, prompts[4], title, vivid=True, hd=True, rewrite=False, no_sleep=True)
get_image(5, prompts[4], title, vivid=False, hd=True, rewrite=False, no_sleep=True)
get_image(6, prompts[4], title, vivid=True, hd=True, rewrite=True, no_sleep=True)
get_image(7, prompts[4], title, vivid=False, hd=True, rewrite=True, no_sleep=True)

# HD and vivid both make a big difference, rewrite is TBD
get_image(8, prompts[6], title, vivid=True, hd=True, rewrite=False, no_sleep=True)
get_image(9, prompts[6], title, vivid=True, hd=True, rewrite=True, no_sleep=True)

# test title add
get_image(10, prompts[5], title, vivid=True, hd=True, rewrite=True, no_sleep=True)
```