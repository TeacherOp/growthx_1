# Mental modal before prompting the right way

- A guide for prompting from my personal experience
- Preparation for the prompt is 10x more important than the prompt itself
- Prompting will automatically happen once you are prepared

## Things to do before you start prompting

- A progressive roadmap of what you want to develop,
  - Example you want to develop an AI powered, trip finder aggregator platform ( experiences like relaxation, creativity etc)
    - Now this would require multiple things
      - The basics like your auth, databases, landing pages, UI / UX, user journeys how it would look, payment gateways, how would bookings will happen etc
        - Now you need to think about the most important parts which are unique and important
          - Data sources, how will you get the listings where does that data come from
          - Will you be cordinating the bookings or redirect users to the source from where the data is found
      - Then even if you want to have AI powered search, you cant build the AI powered search and suggestions untill the base platform is in place, i would leave this aside for now and develop the base platform
        - Then i will implement the AI search and suggestions into the platform, after deciding the UX
- Thinking about your prompts and how to access the knowledge the AI models have
    - Now developing an aggregtor platform is something the AI can do rather easily
        - Why?
            - Becuase there are a lot of aggregator platforms in the world already -> which implies there is a lot of opensource / code on which these models have already trained
    - The AI search and suggestions, that feels new
        - Not a lot of products with ai search and suggestions
        - Not a lot of code on which the model has been trained already to give you the perfect output
        - You want to use the latest standards and best practices, which in most cases are available on dates which are beyond any llm models training cutoff date
        - The search algos might be easier, but AI search, when to embed data, how to embed data, how to chunk it, how to search it, RAG or Combined, or simple search and feed results to AI and generate suggestions? 
         - Now for this what i do is create docs or even as claude code to research available docs, and save important patterns, methods to use the llm apis, how to handle responess, how to use tools etc in docs within folders
         - Which helps me guide the model easily to read and implement the methods correctly

- So in a nutshell, its fairly logical and simple, but you need to know what you are doing, play around with models urself to figure out what limitations there are, what code it might already be trained on a lot, and whatever is new, its safer to create your own docs, or ask the model to research and create docs for more accurate outputs and save a lot of time.

- Another quick example to clarify more little nuances
    - In early days like 2 years ago, when you asked models to create websites, most of the time the button placements, like the most basic thing in a navigation bar would be wrong
    - Then i would tell the model to place it in the right corner of the page
        - The model will place it in the left, and then i will till you placed it in the left and then it would correct it
        - This made me realise i am talking to an api coming from a server sitting somewhere, it has no sense of direction, size or color, it can tell left right, nort south up down its all relative
    - Then i used to prompt with references place th button to the right side of the logo which is on the left end of the nav bar
        - The output? - Perfect in the first time
    - Now with latest models you dont see this basic issue anymore, but there are always new gaps when you solve a problem, you find new problems, the models are not smart or intelligent or not actually "think" - its more of logical ways we are forcing them to access the vast amount of knowledge they have, and thats what is great once you assume the model is dumb, but the most knowledgebale entinty in the world, you need to figure out how to guide it and access the knowledge it has -> For that you need to become smarter, which you can but you cant become more knowledgeable than a model


## Other good practices

- Instead of technical details, 
    - Your prompts should focus more like a PRD from a product manager
    - Add user journeys, for the feature you are developing
        - even if simple journeys, but do that your output will be way better. 
    - The expected system behavior, the tradeoffs of you are doing to implemnent this
    - The not to do, overengineering stuff, why we are implementing only this and what is excluded so the model never generates uncessary extra functionalities, which might be the very logical extensions of your feature but you might not need it, probabilty will force the model to implement it even if you dont want to
    - example
        - You want to setup login and signup
        - Now many times for a quick MVP you wont even need password reset
        - You only want login with google, no email otp or magic links
        - if you dont specify this, your login / signup will like the most available in the industry which have social + email / usermame password logins with password reset pages etc